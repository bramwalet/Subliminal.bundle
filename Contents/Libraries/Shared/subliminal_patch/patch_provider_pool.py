# coding=utf-8

import logging
import traceback
import requests
import socket

from pkg_resources import EntryPoint, iter_entry_points

from subliminal.api import ProviderPool

logger = logging.getLogger(__name__)

class OldToNewProvider(object):
    """
    Simple proxy class to support the .plugin property which would normally exist
    when this was a stevedore.extension
    """
    def __init__(self, provider):
	self.provider = provider
    
    def plugin(self):
	return self.provider
    plugin = property(plugin)


class LegacyProviderManager(object):
    """
    This is the old ProviderManager subliminal used in its pre-1.0 versions, not relying on stevedore.
    Its providers are wrapped inside OldToNewProvider instances, which support the .plugin property
    subliminal expects.

    Old Doc: Manager for providers behaving like a dict with lazy loading
    Loading is done in this order:
    * Entry point providers
    * Registered providers
    .. attribute:: entry_point
        The entry point where to look for providers
    """
    entry_point = 'subliminal.providers'

    def __init__(self, enabled_providers=None):
        #: Registered providers with entry point syntax
        self.registered_providers = ['addic7ed = subliminal.providers.addic7ed:Addic7edProvider',
                                     'opensubtitles = subliminal.providers.opensubtitles:OpenSubtitlesProvider',
                                     'podnapisi = subliminal.providers.podnapisi:PodnapisiProvider',
                                     'thesubdb = subliminal.providers.thesubdb:TheSubDBProvider',
                                     'tvsubtitles = subliminal.providers.tvsubtitles:TVsubtitlesProvider']

	self.enabled_providers = enabled_providers or []

        #: Loaded providers
        self.providers = {}

    @property
    def available_providers(self):
        """Available providers"""
        available_providers = set(self.providers.keys())
        available_providers.update([ep.name for ep in iter_entry_points(self.entry_point)])
        available_providers.update([EntryPoint.parse(c).name for c in self.registered_providers])
        return available_providers

    def __getitem__(self, name):
        """Get a provider, lazy loading it if necessary"""
	
        if name in self.enabled_providers and name in self.providers:
            return self.providers[name]
        for ep in iter_entry_points(self.entry_point):
            if ep.name == name and name in self.enabled_providers:
                self.providers[ep.name] = OldToNewProvider(ep.load())
                return self.providers[ep.name]
        for ep in (EntryPoint.parse(c) for c in self.registered_providers):
            if ep.name == name and name in self.enabled_providers:
                self.providers[ep.name] = OldToNewProvider(ep.load(require=False))
                return self.providers[ep.name]
        raise KeyError(name)

    def __setitem__(self, name, provider):
        """Load a provider"""
        self.providers[name] = provider

    def __delitem__(self, name):
        """Unload a provider"""
        del self.providers[name]

    def __iter__(self):
        """Iterator over loaded providers"""
        return iter(self.providers)

    def register(self, entry_point):
        """Register a provider
        :param string entry_point: provider to register (entry point syntax)
        :raise: ValueError if already registered
        """
        if entry_point in self.registered_providers:
            raise ValueError('Entry point \'%s\' already registered' % entry_point)
        entry_point_name = EntryPoint.parse(entry_point).name
        if entry_point_name in self.available_providers:
            raise ValueError('An entry point with name \'%s\' already registered' % entry_point_name)
        self.registered_providers.insert(0, entry_point)

    def unregister(self, entry_point):
        """Unregister a provider
        :param string entry_point: provider to unregister (entry point syntax)
        """
        self.registered_providers.remove(entry_point)

    def __contains__(self, name):
        return name in self.providers

provider_manager = LegacyProviderManager()



class PatchedProviderPool(ProviderPool):
    """
    this is the subliminal ProviderPool but slightly patched to use our LegacyProviderManager,
    because the new ProviderManager in the current subliminal package relies on stevedore, which has
    problems detecting subliminal's provider extensions when running in the Plex sandbox
    """
    def __init__(self, providers=None, provider_configs=None):
        #: Name of providers to use
        self.providers = providers or provider_manager.available_providers

        #: Provider configuration
        self.provider_configs = provider_configs or {}

        #: Initialized providers
        self.initialized_providers = {}

        #: Discarded providers
        self.discarded_providers = set()

        #: Dedicated :data:`provider_manager` as :class:`~stevedore.enabled.EnabledExtensionManager`
        #self.manager = EnabledExtensionManager(provider_manager.namespace, lambda e: e.name in self.providers)
	self.manager = provider_manager if not providers else LegacyProviderManager(self.providers)
	
    def list_subtitles(self, video, languages):
        """List subtitles.
        :param video: video to list subtitles for.
        :type video: :class:`~subliminal.video.Video`
        :param languages: languages to search for.
        :type languages: set of :class:`~babelfish.language.Language`
        :return: found subtitles.
        :rtype: list of :class:`~subliminal.subtitle.Subtitle`
        """
        subtitles = []

        for name in self.providers:
            # check discarded providers
            if name in self.discarded_providers:
                logger.debug('Skipping discarded provider %r', name)
                continue

            # check video validity
            if not self.manager[name].plugin.check(video):
                logger.info('Skipping provider %r: not a valid video', name)
                continue

            # check supported languages
            provider_languages = self.manager[name].plugin.languages & languages
            if not provider_languages:
                logger.info('Skipping provider %r: no language to search for', name)
                continue

            # list subtitles
            logger.info('Listing subtitles with provider %r and languages %r', name, provider_languages)
            try:
                provider_subtitles = self[name].list_subtitles(video, provider_languages)
            except (requests.Timeout, socket.timeout):
                logger.error('Provider %r timed out, discarding it', name)
                self.discarded_providers.add(name)
                continue
            except Exception, e:
                logger.exception('Unexpected error in provider %r, discarding it, because of: %s', name, traceback.format_exc())
                self.discarded_providers.add(name)
                continue
            subtitles.extend(provider_subtitles)

        return subtitles
