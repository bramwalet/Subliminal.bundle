# Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat)](https://github.com/pannal/Sub-Zero.bundle/releases)
[![master](https://img.shields.io/badge/master-stable-green.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2017.svg)]()

<img src="https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif" align="left" height="100"> <font size="5"><b>Subtitles done right!</b></font><br />

Checkout **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)** by [@ukdtom](https://github.com/ukdtom) <br />
<br style="clear:left;"/>

## Introduction
#### What's Sub-Zero?
Sub-Zero is a metadata agent and channel at the same time, for the popular Plex Media Server environment.

#### Why not use the builtin OpenSubtitles agent?
Because it doesn't deliver. Especially for very new media items it may pick up none or bad subtitles for your media. Also it doesn't know when "better" subtitles get released for your media file.

## Key-Features
This is just a tiny peek at the full feature-set of Sub-Zero.

#### Searching/Matching
It searches up to 8 individual subtitle provider sites and APIs, selects the best matching subtitle and downloads it for you.

The matching is done by looking at the filename of your media files, as well as media information inside the container.
Every subtitle gets a score assigned, based on the matching algorithm. The one with the highest score gets picked automatically. The more information your media filenames have, the better. `Moviename.mkv` has a higher chance of getting bad subtitles than `Moviename.2015.720p.BluRay-RLSGRP`.

#### Storage-Options
*You* can decide where Sub-Zero stores its downloaded subtitles. By default it saves the subtitles externally, as "sidecars", besides the actual media file.
Additionally you can specify a fixed location for *all* your subtitles, or pre-defined or custom sub-folders.

If you don't want SRT files lying around in your library, you also have the option to store subtitles inside the internal metadata storage of the Plex Media Server.

#### Personalization
Via the preferences you can configure almost every parameter Sub-Zero uses when handling your subtitles.

From an infinite number of different languages to search for, to hearing impaired settings, foreign/forced-only captions, embedded subtitle handling and many more.

#### Channel menu
The automatic matching Sub-Zero does has been improved massively over the last years and reaches an extremely high accuracy for recently-released items, in the first 6 hours. It still might be, that you want some manual managability over your library and its subtitles. This is where the channel menu comes into play.

It allows you to trigger background tasks, browse your library based on several different starting points, adds a recently-viewed menu for instant access to your recently played media and allows you to list and select available subtitles for any item in your library.

#### Subtitle Modifications
With Sub-Zero 2.0 automatic and manual subtitle modifications have been included.
They currently consist of six individual mods:
- **Offset**: Your subtitle is out of sync? Manually adjust the timing of your subtitles
- **FPS**: Your subtitle is getting slower over time, or faster over time? Maybe the framerate is wrong. The FPS mod can fix that.
- **Hearing Impaired**: Removes HI-tags from subtitles (such as `(SIRENS WAIL)`, `DOCTOR: Rose!`)
- **Color**: Adds color to your subtitles (for playback devices/software that don't ship their own color modes; only works for players that support color tags)
- **Common**: fixes common issues in subtitles, such as punctuation (`-- I don't know!` -> `... I don't know!`; `over 9 000!` -> `over 9000!`)
- **OCR**: fixes problems in subtitles introduced by OCR (custom implementation of [SubtitleEdit](https://github.com/SubtitleEdit/subtitleedit)'s dictionaries) (`hands agaInst the waII!` -> `hands against the wall!`)

Hearing Impaired, Common and OCR can be applied automatically on every subtitle downloaded. All mods are manually managable via the channel menu.

Mods are applied on-the-fly, the original content of the subtitle stays available, so mods are completely reversible.


## Installation
Simply go to the Plex Channels in your Plex Media Server, search for Sub-Zero and install it.
For further help or manual installation, [please go to the wiki](https://github.com/pannal/Sub-Zero.bundle/wiki).

## Changelog

2.0.19.1267 RC6
- core: add new SZ subtitle storage format
  - smaller data files and less cumbersome
  - it will auto migrate when old data is accessed - to speed this up, use "Trigger subtitle storage migration (expensive)" in advanced menu)
- core: performance optimizations
- addic7ed: when release group matches, assume the format matches, too (leftover change from RC5)
- submod: fix patterns for beginlines/endlines
- submod: add our own dictionaries to OCR fixes (english)
- submod: hearing impaired: also remove full-caps with punctuation inside
- submod: correctly handle partiallines
- submod: in numbers with spaces (incorrect), also allow for some punctuation (,.:')


2.0.18.1245 RC5
- core: add more debug info
- core: fix subtitle modifications (was broken in RC4, created non-usable subtitles)
- submod: add ANSI colors
- menu/submod: add color mod menu
- submod: exclusive mods now are mutually exclusive and get cleaned on duplicate
- menu/core: naming

For everyone who runs RC4: your subtitles are broken. Go to the advanced menu and trigger `Re-Apply mods of all stored subtitles` to fix them.


2.0.17.1234 RC4
- core: backport provider-download-retry implementation
- core: implement custom user agent (for OpenSubtitles)
- core/menu: correct handling of media with multiple files
- core: fix SearchAllRecentlyMissing; also wait 5 seconds between searches
- core: SearchAllRecentlyMissing: honor physical ignores
- submod: pattern fixes
- submod: better unicode handling
- submod: add color mod (only automatic by now)


2.0.15.1216 RC3
- core: fixes
- scheduler: revert some of the aggressive changes in RC2
- submod: be smarter about WholeLine matches


2.0.15.1209 RC2
- core: fixes
- core: submod-common: fix multiple dots at start of line
- core/menu: add subtitle modification debug setting
- core/menu: when manually listing available subtitles in menu, display those with wrong FPS also (opensubtitles), because you can fix them later
- core/menu: advanced-menu: add apply-all-default-mods menu item; add re-apply all mods menu item
- core: always look for currently (not-) existing subtitles when called; hopefully fixes #276
- scheduler/menu: be faster; also launch scheduled tasks in threads, not just manually launched ones
- core: don't delete subtitles with .custom or .embedded in their filenames when running auto cleanup, if the correct media file exists
- menu: add back-to-previous menu items


2.0.12.1180 RC1
- core: update subliminal to version 2
- core: update all dependencies
- core: add new providers: legendastv (pt-BR), napiprojekt (pl), shooter (cn), subscenter (heb)
- core: rewritten all subliminal patches for version 2
- menu: add icons for menu items; update main channel icon
- core: use SSL again for opensubtitles
- core: improved matching due to subliminal 2 (and SZ custom) tvdb/omdb refiners
- menu: add "Get my logs" function to the advanced menu, which zips up all necessary logs suitable for posting in the forums
- core: on non-windows systems, utilize a file-based cache database for provider media lists and subliminal refiner results
- core: add manual and automatic subtitle modification framework (fix common OCR issues, remove hearing impaired etc.)
- menu: add subtitle modifications (subtitle content fixes, offset-based shifting, framerate conversion)
- menu: add recently played menu
- improve almost everything Sub-Zero did in 1.4 :)


1.4.27.973
- core: ignore "obfuscated" and "scrambled" tags in filenames when searching for subtitles
- core: exotic embedded subtitles are now also considered when searching (and when the option is enabled); fixes #264


1.4.27.967
- core: remember the last 10 played items; only consider on_playback for "playing" state within the first 60 seconds of an item


1.4.27.965
- core: on_playback activity bugfixes


[older changes](CHANGELOG.md)


If you like this, buy me a beer: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG)

Subtitles provided by [OpenSubtitles.org](http://www.opensubtitles.org/), [Podnapisi.NET](https://www.podnapisi.net/), [TVSubtitles.net](http://www.tvsubtitles.net/), [Addic7ed.com](http://www.addic7ed.com/), [Legendas TV](http://legendas.tv/), [Napi Projekt](http://www.napiprojekt.pl/), [Shooter](http://shooter.cn/), [SubsCenter](http://www.subscenter.org)