# pannal's fork of Subliminal.bundle

Please install [LocalMediaExtended.bundle](https://github.com/pannal/LocalMediaExtended.bundle) and use it **INSTEAD** of LocalMedia.

Use the following agent order:

1. Subliminal TV/Movie Subtitles
2. Local Media Assets Extended
3. anything else
4. again, **DISABLE Local Media Assets**!

### Quick installation
* go to ```Library/Application Support/Plex Media Server/Plug-ins/```
* ```rm -r Subliminal.bundle```
* ```wget https://github.com/pannal/Subliminal.bundle/releases/download/1.1-rc3/Subliminal.bundle-1.1-rc3.zip```
* ```unzip Subliminal.bundle-1.1-rc3.zip```
* more indepth: look below on ```Installation```

### Encountered a bug?
* be sure to post your logs: ```Library/Application Support/Plex Media Server/Logs/PMS Plugin Logs/com.plexapp.agents.subliminal.log```; there may be multiple logs (com.plexapp.agents.subliminal.log.*) depending on the amount of Videos you're refreshing
* **Remember: before you open a bug-ticket please double-check, that you've deleted the Subliminal.bundle folder BEFORE every update** (to avoid .pyc leftovers)

## Changelog
#### RC-3
- addic7ed/tvsubtitles: punctuation fixes (correctly get show ids for series like "Mr. Poopster" now)
- podnapisi: fix logging
- opensubtitles: add login credentials (for VIPs)
- add retry functionality to retry failed subtitle downloads, including configurable amount of retries until discarding of provider
- move possibly not needed setting "Restrict to one language" to the bottom
- more detailed logging
- some cleanup

RC-2
- fix empty custom subtitle folder creation
- fix detection of existing embedded subtitles (switch to https://github.com/tonswieb/enzyme)
- better logging
- set default TV score to 15; movie score to 30

RC-1
- fix subliminal's logging error on min_score not met (fixes #15)
- separated tv and movies subtitle scores settings (fixes #16)
- add option to save only one subtitle per video (skipping the ".lang." naming scheme plex supports) (fixes #3)

beta5
- fix storing subtitles besides the actual video file, not subfolder (fixes #14)
- "custom folder" setting now always used if given (properly overrides "subtitle folder" setting)
- also scan (custom) given subtitle folders for existing subtitles instead of redownloading them on every refresh (fixes #9, #2)

beta4
- ~~increased score of addic7ed subtitles a bit~~ (not existing currently)
- **support for newest Subliminal ([1.0.1](27a6e51cd36ffb2910cd9a7add6d797a2c6469b7)) and guessit ([0.11.0](2814f57e8999dcc31575619f076c0c1a63ce78f2))**
- **plugin now also [works with com.plexapp.agents.thetvdbdvdorder](924470d2c0db3a71529278bce4b7247eaf2f85b8)**
- providers fixed for subliminal 1.0.1 ([at least addic7ed](131504e7eed8b3400c457fbe49beea3b115bc916))
- providers [don't simply fail and get excluded on non-detected language](1a779020792e0201ad689eefbf5a126155e89c97)
- support for addic7ed languages: [French (Canadian)](b11a051c233fd72033f0c3b5a8c1965260e7e19f)
- support for additional languages: [pt-br (Portuguese (Brasil)), fa (Persian (Farsi))](131504e7eed8b3400c457fbe49beea3b115bc916)
- support for [three (two optional) subtitle languages](e543c927cf49c264eaece36640c99d67a99c7da2)
- optionally use [random user agent for addic7ed provider](83ace14faf75fbd75313f0ceda9b78161895fbcf) (should not be needed)

Subliminal.bundle
=================

Plex Metadata agent plugin based on Subliminal. This agent will search on the following sites for the best matching subtitles:
- OpenSubtitles
- TheSubDB
- Podnapisi.NET
- Addic7ed
- TVsubtitles.net

All providers can be disabled or enabled on a per provider setting. Certain preferences change the behaviour of subliminal, for instance the minimum score of subtitles to download, or whether to download hearing impaired subtitles or not. The agent stores the subtitles as metadata, but can be configured (See Configuration) to store it next to the media files. 

Installation
------------
See [article](https://support.plex.tv/hc/en-us/articles/201187656-How-do-I-manually-install-a-channel-) on Plex website. 

Configuration 
-------------
Several options are provided in the preferences of this agent. 
* Addic7ed username/password: Provide your addic7ed username here, otherwise the provider won't work. Please make sure your account is activated, before using the agent.
* Subtitle language (1)/(2): Your preferred languages to download subtitles for. 
* Provider: Enable ...: Enable/disable this provider. Affects both movies and series. 
* Scan: Include embedded subtitles: When enabled, subliminal finds embedded subtitles that are already present within the media file. 
* Scan: Include external subtitles: When enabled, subliminal finds subtitles located near the media file on the filesystem.
* Minimum score for download: When configured, what is the minimum score for subtitles to download them? Lower scored subtitles are not downloaded.
* Download hearing impaired subtitles: When configured, hearing impaired subtitles will be downloaded. 
* Store subtitles next to media files (instead of metadata): See Store as metadata or on filesystem
* Subtitle folder: See Store as metadata or on filesystem
* Custom Subtitle folder: See Store as metadata or on filesystem 

Store as metadata or on filesystem
----------------------------------
By default, Plex stores posters, fan art and subtitles as metadata in a separate folder which is not managed by the user. This is the default behaviour of this agent. However, expert users can enable 'Store subtitles next to media files'. The agent will write the subtitle files in the media folder. The setting 'Subtitle folder' configures in which folder (current folder or other subfolder) the subtitles are stored. The expert user can also supply 'Custom Subtitle folder' which can also be an absolute path.

Please note that you need a way to pick up external subtitles to show up in the Plex Media server. When the subtitles are stored next to your media folders, it is sufficient to enable Local Media agent and place it below the Subliminal agent in the agent priorities. When a subfolder (either custom or predefined) is used, you need [LocalMediaExtended](https://github.com/pannal/LocalMediaExtended.bundle).

License
-------
MIT

Libraries
---------
Uses the following libraries and their LICENSE:
- [babelfish](https://pypi.python.org/pypi/babelfish/) (BSD-3-Clause)
- [beautifulsoup4](https://pypi.python.org/pypi/beautifulsoup4/) (MIT)
- [chardet](https://pypi.python.org/pypi/chardet/) (LGPL)
- [dogpile.core](https://pypi.python.org/pypi/dogpile.core/) (BSD)
- [dogpile.cache](https://pypi.python.org/pypi/dogpile.cache/) (BSD)
- [enzyme](https://pypi.python.org/pypi/enzyme/) (Apache 2.0)
- [guessit](https://pypi.python.org/pypi/guessit/) (LGPLv3)
- [html5lib](https://pypi.python.org/pypi/html5lib/) (MIT)
- [pysrt](https://pypi.python.org/pypi/pysrt/) (GPLv3)
- [requests](https://pypi.python.org/pypi/requests/) (Apache 2.0)
- [stevedore](https://pypi.python.org/pypi/stevedore/) (Apache)
- [subliminal](https://pypi.python.org/pypi/subliminal/) (MIT)
- [xdg](https://pypi.python.org/pypi/pyxdg/) (LGPLv2)
- [setuptools](https://pypi.python.org/pypi/setuptools/) (PSF ZPL)
