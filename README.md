#Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat)](https://github.com/pannal/Sub-Zero.bundle/releases) [![Maintenance](https://img.shields.io/maintenance/yes/2016.svg?maxAge=2592000)]()

![logo](https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif)

##### Subtitles done right

## Information
Please see **[the Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)** for further information

## Changelog

1.3.33.522

- core: fix library permission detection on windows; fixes #151
- core: "Restrict to one language" now behaves like it should (one found subtitle of any language is treated as sufficient); fixes #149
- core: add support for other subtitle formats such as ssa/ass/microdvd, convert to srt; fixes #138
- core: hopefully more consistent force-refresh handling (intent); fixes #118

[older changes](CHANGELOG.md)


If you like this, buy me a beer: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG)


**************************** Below is a placeholder of information not yet migrated to the Wiki *************************

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

Scheduler
---------------------------------------
The built-in scheduler is capable of running a number of tasks periodically in a separate Thread of the plugin.
This currently is used to automatically periodically search for new subtitles for your media items.
See configuration above.

##### Ignore list
There are numerous occasions where one wouldn't want a certain item or even a library be included in the periodic "Search for missing subtitles"-task or the "Items with missing subtitles" menu function.
Anime libraries are a good example of that, or home videos. Perhaps you've got your favourite series in your native language and don't want subtitles for it.

The ignore list can be managed by going through your library using the "Browse all items" menu and the "Display ignore list" menu. 

BETA: Physically Ignoring Media
-------------------------
Sometimes subtitles aren't needed or wanted for parts of your library.

When creating a file named `subzero.ignore`, `.subzero.ignore`, or `.nosz` in any of your library's folders, be it
the section itself, a TV show, a movie, or even a season, Sub-Zero will skip processing the contents of that folder.
 
BETA notes: This may still mean that the scheduler task for missing subtitles triggers refresh actions on those items,
but the refresh handler itself will skip those.
