

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



## Changelog

1.3.33.522

- core: fix library permission detection on windows; fixes #151
- core: "Restrict to one language" now behaves like it should (one found subtitle of any language is treated as sufficient); fixes #149
- core: add support for other subtitle formats such as ssa/ass/microdvd, convert to srt; fixes #138
- core: hopefully more consistent force-refresh handling (intent); fixes #118

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




BETA: Physically Ignoring Media
-------------------------
Sometimes subtitles aren't needed or wanted for parts of your library.

When creating a file named `subzero.ignore`, `.subzero.ignore`, or `.nosz` in any of your library's folders, be it
the section itself, a TV show, a movie, or even a season, Sub-Zero will skip processing the contents of that folder.
 
BETA notes: This may still mean that the scheduler task for missing subtitles triggers refresh actions on those items,
but the refresh handler itself will skip those.


