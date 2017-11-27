# coding=utf-8
from babelfish import Language

import subliminal_patch as subliminal

from support.config import config
from support.helpers import cast_bool
from subtitlehelpers import get_subtitles_from_metadata
from subliminal_patch import compute_score
from support.plex_media import get_blacklist_from_part_map


def download_best_subtitles(video_part_map, min_score=0, throttle_time=None):
    hearing_impaired = Prefs['subtitles.search.hearingImpaired']
    ietf_as_alpha3 = cast_bool(Prefs["subtitles.language.ietf_normalize"])
    languages = set([Language.fromietf(str(l)) for l in config.lang_list])
    if not languages:
        return

    # should we treat IETF as alpha3? (ditch the country part)
    alpha3_map = {}
    if ietf_as_alpha3:
        for language in languages:
            if language.country:
                alpha3_map[language.alpha3] = language.country
                language.country = None

    missing_languages = False
    for video, part in video_part_map.iteritems():
        if not Prefs['subtitles.save.filesystem']:
            # scan for existing metadata subtitles
            meta_subs = get_subtitles_from_metadata(part)
            for language, subList in meta_subs.iteritems():
                if subList:
                    video.subtitle_languages.add(language)
                    Log.Debug("Found metadata subtitle %s for %s", language, video)

        have_languages = video.subtitle_languages.copy()
        if ietf_as_alpha3:
            for language in have_languages:
                if language.country:
                    alpha3_map[language.alpha3] = language.country
                    language.country = None

        missing_subs = (set(str(l) for l in languages) - set(str(l) for l in have_languages))

        # all languages are found if we either really have subs for all languages or we only want to have exactly one language
        # and we've only found one (the case for a selected language, Prefs['subtitles.only_one'] (one found sub matches any language))
        found_one_which_is_enough = len(video.subtitle_languages) >= 1 and Prefs['subtitles.only_one']
        if not missing_subs or found_one_which_is_enough:
            if found_one_which_is_enough:
                Log.Debug('Only one language was requested, and we\'ve got a subtitle for %s', video)
            else:
                Log.Debug('All languages %r exist for %s', languages, video)
            continue
        missing_languages = True
        break

    if missing_languages:
        # re-add country codes to the missing languages, in case we've removed them above
        if ietf_as_alpha3:
            for language in languages:
                language.country = alpha3_map.get(language.alpha3, None)

        Log.Debug("Download best subtitles using settings: min_score: %s, hearing_impaired: %s, languages: %s" %
                  (min_score, hearing_impaired, languages))

        # prepare blacklist
        blacklist = get_blacklist_from_part_map(video_part_map, languages)

        return subliminal.download_best_subtitles(video_part_map.keys(), languages, min_score, hearing_impaired, providers=config.providers,
                                                  provider_configs=config.provider_settings, pool_class=config.provider_pool,
                                                  compute_score=compute_score, throttle_time=throttle_time, blacklist=blacklist)
    Log.Debug("All languages for all requested videos exist. Doing nothing.")