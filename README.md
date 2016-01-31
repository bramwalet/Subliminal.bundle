Sub-Zero for Plex, 1.3.27.491
=================

![logo](https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif)

##### Subtitles done right
Originally based on @bramwalet's awesome [Subliminal.bundle](https://github.com/bramwalet/Subliminal.bundle)

Plex forum thread: https://forums.plex.tv/discussion/186575

If you like this, buy me a beer: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG)

### Installation
* go to ```Library/Application Support/Plex Media Server/Plug-ins/```
* ```rm -r Sub-Zero.bundle``` (remove the folder)
* get the release you want from *https://github.com/pannal/Sub-Zero.bundle/releases/*
* unzip the release
* restart your plex media server!!!
* more indepth: see [article](https://support.plex.tv/hc/en-us/articles/201187656-How-do-I-manually-install-a-channel-) on Plex website. 

### Usage
Use the following agent order:

1. Sub-Zero TV/Movie Subtitles
2. Local Media Assets
3. anything else

##### Recommended steps
Create an account and provide your credentials (in the plugin configuration) for:

* [Addic7ed](http://www.addic7ed.com/newaccount.php)
* [Opensubtitles](http://www.opensubtitles.org/en/newuser)
* [Plex](https://plex.tv/users/sign_up)

### Attention on the initial refresh
When you first use this plugin and run a refresh on all of your media, you may be
blacklisted out of excessive usage by some or all of the subtitle providers depending on your library's size.
This will result in a bunch of errors in the log files as well as missing subtitles.

Just be patient, after a day most of those providers will allow you to access them again and you can
refresh the remaining items. If you use the default settings, this will also skip the items
it has already downloaded all the wanted languages for. Also, as subtitles will be missing, the scheduler should pick up
the items with missing subtitles automatically.

### Encountered a bug?
* be sure to post your logs: 
  * set your log_level to DEBUG in the settings
  * get ```Library/Application Support/Plex Media Server/Logs/PMS Plugin Logs/com.plexapp.agents.subzero.log```; there may be multiple logs (com.plexapp.agents.subzero.log.*) depending on the amount of Videos you're refreshing
* **Remember: before you open a bug-ticket please double-check, that you've deleted the Sub-Zero.bundle folder BEFORE every update** (to avoid .pyc leftovers)

## Changelog

1.3.27.491

- menu/core: make Sub-Zero channel menu optional (setting: "Enable Sub-Zero channel (disabling doesn't affect the subtitle features)?")
- OpenSubtitles: detect and match video/subtitle FPS (framerate) to reduce out of sync subtitle matches
- core: internal fixes; add _markerlib library (rare)
- core: don't score tvshow episode title matches, should improve episode subtitle matches quite a bit (and reduce out of sync subtitles)
- OpenSubtitles: make tag/exact filename matches optional (setting: "I keep the exact (release-) filename of my media files")
- menu: unicode video title errors fixed
- TVSubtitles: correctly match certain show IDs (such as "Series Name (US)")
- core: don't break subtitle evaluation on crashed guessing


[older changes](CHANGELOG.md)

Description
------------

Plex Metadata agent plugin based on Subliminal. This agent will search on the following sites for the best matching subtitles:
- OpenSubtitles
- ~~TheSubDB~~
- Podnapisi.NET
- Addic7ed
- TVsubtitles.net

All providers can be disabled or enabled on a per provider setting. Certain preferences change the behaviour of subliminal, for instance the minimum score of subtitles to download, or whether to download hearing impaired subtitles or not. The agent stores the subtitles as metadata, but can be configured (See Configuration) to store it next to the media files. 


Configuration 
-------------
Several options are provided in the preferences of this agent. 

* Enable Sub-Zero channel (disabling doesn't affect the subtitle features)?: Show or hide the Sub-Zero channel from your PMS
* Addic7ed username/password: Provide your addic7ed username here, otherwise the provider won't work. Please make sure your account is activated, before using the agent.
* Plex.tv username/password: Generally recommended to be provided; needed if you use Plex Home to make the API work (the whole channel menu depends on it)
* Opensubtitles username/password: Generally recommended to be provided (not necessarily needed, but avoids errors)
* Subtitle language (1)/(2)/(3): Your preferred languages to download subtitles for. 
* Additional Subtitle Languages: Additional languages to download; comma-separated; use [ISO-639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes))
* Provider: Enable ...: Enable/disable this provider. Affects both movies and series. 
* Addic7ed: (TV only) boost over hash score if requirements met: if an Addic7ed subtitle matches the video's series, season, episode, year, boost its score, possibly over OpenSubtitles/TheSubDB direct hash match. Recommended for higher quality subtitle results. 
* I keep the exact (release-) filename of my media files: If you don't rename your media files automatically or manually and keep the original release's file names, enabling this option may help finding suitable subtitles for your media. Otherwise: disable this. 
* Scan: Include embedded subtitles: When enabled, subliminal finds embedded subtitles (ignoring forced) that are already present within the media file. 
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
* Ignore folders (...): If a folder contains one of the files named `subzero.ignore`, `.subzero.ignore`, `.nosz`, don't process them. This applies to sections/libraries, movies, series, seasons, episodes 
* Scheduler: 
  * Periodically search for recent items with missing subtitles: self-explanatory, executes the task "Search for missing subtitles" from the channel menu regularly. Configure how often it should do that. For the average library 6 hours minimum is recommended, to not hammer the providers too heavily
  * Item age to be considered recent: The "Search for missing subtitles"-task only considers those items in the recently-added list, that are at most this old
  * Recent items to consider per library: How many items to consider for every section/library you have - used in "Search for missing subtitles"-task and "Items with missing subtitles"-menu. Change at your own risk!
* How verbose should the logging be?: Controls how much info we write into the log files (default: only warnings)
* Log to console (for development/debugging): You know when you need it

Scheduler
---------------------------------------
The built-in scheduler is capable of running a number of tasks periodically in a separate Thread of the plugin.
This currently is used to automatically periodically search for new subtitles for your media items.
See configuration above.

##### Ignore list
There are numerous occasions where one wouldn't want a certain item or even a library be included in the periodic "Search for missing subtitles"-task or the "Items with missing subtitles" menu function.
Anime libraries are a good example of that, or home videos. Perhaps you've got your favourite series in your native language and don't want subtitles for it.

The ignore list can be managed by going through your library using the "Browse all items" menu and the "Display ignore list" menu. 


The channel
-----------
Since 1.3.0 Sub-Zero not only comes as an agent plugin, but also has channel properties.
By accessing the Sub-Zero channel you can get viable information about the scheduler state, search for missing subtitles,
trigger forced-searches for individual items, and many more features yet to come.

Remoting the channel
--------------------
The features available in the channel menu are in fact accessible and usable from the outside,
just as any other channel with routes.
This means, that if you're not happy with the scheduler's interval for example, you can take the following URL:
`http://plex_ip:32400/video/subzero/missing/refresh?X-Plex-Token=XXXXXXXXXXXXXXX` (the X-Plex-Token part may not be needed outside of
a Plex Home) and open the URL using your favourite command line tool or script (curl, wget, ...).
This will trigger the same background task which would be started by the scheduler or by clicking the item in the channel menu.

You can find all available routes by querying `http://plex_ip:32400/video/subzero` (look for the key="" entries). 


Store as metadata or on filesystem
----------------------------------
By default, Plex stores posters, fan art and subtitles as metadata in a separate folder which is not managed by the user. 
In Sub-Zero, though, 'Store subtitles next to media files' is enabled by default.
The agent will write the subtitle files in the media folder next to the media file itself. 
The setting 'Subtitle folder' configures in which folder (current folder or other subfolder) the subtitles are stored. The expert user can also supply 'Custom Subtitle folder' which can also be an absolute path.

**When a subfolder (either custom or predefined) is used, the automatic scheduled refresh of Plex won't pick up your subtitles, only a manual refresh will!**


BETA: Physically Ignoring Media
-------------------------
Sometimes subtitles aren't needed or wanted for parts of your library.

When creating a file named `subzero.ignore`, `.subzero.ignore`, or `.nosz` in any of your library's folders, be it
the section itself, a TV show, a movie, or even a season, Sub-Zero will skip processing the contents of that folder.
 
BETA notes: This may still mean that the scheduler task for missing subtitles triggers refresh actions on those items,
but the refresh handler itself will skip those.

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
