Sub-Zero for Plex, 1.3.0.216
=================

![logo](https://raw.githubusercontent.com/pannal/Sub-Zero/master/Contents/Resources/subzero.gif)

##### Subtitles done right
Originally based on @bramwalet's awesome [Subliminal.bundle](https://github.com/bramwalet/Subliminal.bundle)

Plex forum thread: https://forums.plex.tv/discussion/186575

### Installation
* go to ```Library/Application Support/Plex Media Server/Plug-ins/```
* ```rm -r Sub-Zero.bundle```
* get the release you want from *https://github.com/pannal/Sub-Zero/releases/*
* unzip the release
* more indepth: see [article](https://support.plex.tv/hc/en-us/articles/201187656-How-do-I-manually-install-a-channel-) on Plex website. 

### Usage
Use the following agent order:

1. Sub-Zero TV/Movie Subtitles
2. Local Media Assets
3. anything else

### Encountered a bug?
* be sure to post your logs: ```Library/Application Support/Plex Media Server/Logs/PMS Plugin Logs/com.plexapp.agents.subzero.log```; there may be multiple logs (com.plexapp.agents.subzero.log.*) depending on the amount of Videos you're refreshing
* **Remember: before you open a bug-ticket please double-check, that you've deleted the Sub-Zero.bundle folder BEFORE every update** (to avoid .pyc leftovers)

## Changelog
1.3.0.216
- add channel menu
- add generic task scheduler
- add functionality to search for missing subtitles (via recently added items)
- add artwork
- change license to The Unlicense
- ...

1.2.11.180
- fix #49 (metadata storage didn't work)
- add better detection for existing subtitles stored in metadata

[older changes](CHANGELOG.md)


Description
------------

Plex Metadata agent plugin based on Subliminal. This agent will search on the following sites for the best matching subtitles:
- OpenSubtitles
- TheSubDB
- Podnapisi.NET
- Addic7ed
- TVsubtitles.net

All providers can be disabled or enabled on a per provider setting. Certain preferences change the behaviour of subliminal, for instance the minimum score of subtitles to download, or whether to download hearing impaired subtitles or not. The agent stores the subtitles as metadata, but can be configured (See Configuration) to store it next to the media files. 


Configuration 
-------------
Several options are provided in the preferences of this agent. 
* Addic7ed username/password: Provide your addic7ed username here, otherwise the provider won't work. Please make sure your account is activated, before using the agent.
* Subtitle language (1)/(2)/(3): Your preferred languages to download subtitles for. 
* Additional Subtitle Languages: Additional languages to download; comma-separated; use [ISO-639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes))
* Provider: Enable ...: Enable/disable this provider. Affects both movies and series. 
* Addic7ed: boost over hash score if requirements met: if an Addic7ed subtitle matches the video's series, season, episode, year, and format (e.g. WEB-DL), boost its score, possibly over OpenSubtitles/TheSubDB direct hash match
* Scan: Include embedded subtitles: When enabled, subliminal finds embedded subtitles that are already present within the media file. 
* Scan: Include external subtitles: When enabled, subliminal finds subtitles located near the media file on the filesystem.
* Minimum score for download: When configured, what is the minimum score for subtitles to download them? Lower scored subtitles are not downloaded.
* Download hearing impaired subtitles: 
  * "prefer": score subtitles for hearing impaired higher
  * "don't prefer": score subtitles for hearing impaired lower
  * "force HI": skip subtitles if the hearing impaired flag isn't set
  * "force non-HI": skip subtitles if the hearing impaired flag is set
* Store subtitles next to media files (instead of metadata): See Store as metadata or on filesystem
* Subtitle folder: (default: current media file's folder) See Store as metadata or on filesystem
* Custom Subtitle folder: See Store as metadata or on filesystem 
* Treat IETF language tags as ISO 639-1: Treats subtitle files with IETF language identifiers, such as pt-BR, as their ISO 639-1 counterpart. Thus "pt-BR" will be shown as "Portuguese" instead of "Unknown"

Store as metadata or on filesystem
----------------------------------
By default, Plex stores posters, fan art and subtitles as metadata in a separate folder which is not managed by the user. 
In Sub-Zero, though, 'Store subtitles next to media files' is enabled by default.
The agent will write the subtitle files in the media folder next to the media file itself. 
The setting 'Subtitle folder' configures in which folder (current folder or other subfolder) the subtitles are stored. The expert user can also supply 'Custom Subtitle folder' which can also be an absolute path.

**When a subfolder (either custom or predefined) is used, the automatic scheduled refresh of Plex won't pick up your subtitles, only a manual refresh will!**

License
-------
The Unlicense

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
- [plexinc-agents/LocalMedia.bundle](https://github.com/plexinc-agents/LocalMedia.bundle) (Plex)
- [fuzeman/plex.py](https://github.com/fuzeman/plex.py) (plex.py)
