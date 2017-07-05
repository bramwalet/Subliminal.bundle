# Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat&label=stable)](https://github.com/pannal/Sub-Zero.bundle/releases/latest)<!--[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle/all.svg?maxAge=2592000&label=testing+2.0+RC9)](https://github.com/pannal/Sub-Zero.bundle/releases)--> [![master](https://img.shields.io/badge/master-stable-green.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2017.svg)]()
[![Slack Status](https://szslack.fragstore.net/badge.svg)](https://szslack.fragstore.net)

<img src="https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif" align="left" height="100"> <font size="5"><b>Subtitles done right!</b></font><br />

Check out **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)** by [@ukdtom](https://github.com/ukdtom) <br />
<br style="clear:left;"/>

If you like this, buy me a beer: <br>[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG) <br>or become a Patreon starting at **1 $ / month** <br><a href="https://www.patreon.com/subzero_plex" target="_blank"><img src="http://www.wenspencer.com/wp-content/uploads/2017/02/patreon-button.png" height="42" /></a>

## Introduction
#### What's Sub-Zero?
Sub-Zero is a metadata agent and channel at the same time, for the popular Plex Media Server environment.

#### Why not use the builtin OpenSubtitles agent?
Because it doesn't deliver. Especially for very new media items it may pick up none or bad subtitles for your media. Also it doesn't know when "better" subtitles get released for your media file.

*Mostly all of the key-features listed below don't apply to the default OpenSubtitles subtitle agent in Plex.*

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

#### Automation
Sub-Zero comes with its own background task scheduler. It periodically searches for missing subtitles and better subtitles for your media files.

#### Personalization
Via the preferences you can configure almost every parameter Sub-Zero uses when handling your subtitles.

From an infinite number of different languages to search for, to hearing impaired settings, foreign/forced-only captions, embedded subtitle handling and many more.

#### Channel menu
The automatic matching Sub-Zero does has been improved massively over the last years and reaches an extremely high accuracy for recently-released items, in the first 6 hours. It still might be, that you want some manual managability over your library and its subtitles. This is where the channel menu comes into play.

It allows you to trigger background tasks, browse your library based on several different starting points, adds a recently-viewed menu for instant access to your recently played media and allows you to list and select available subtitles for any item in your library.

#### Modification and Fixing
With Sub-Zero 2.0 automatic and manual subtitle modifications have been included.
They currently consist of six individual mods:
- **Offset**: Your subtitle is out of sync? Manually adjust the timing of your subtitles
- **FPS**: Your subtitle is getting slower over time, or faster over time? Maybe the framerate is wrong. The FPS mod can fix that.
- **Hearing Impaired**: Removes HI-tags from subtitles (such as `(SIRENS WAIL)`, `DOCTOR: Rose!`)
- **Color**: Adds color to your subtitles (for playback devices/software that don't ship their own color modes; only works for players that support color tags)
- **Common**: fixes common issues in subtitles, such as punctuation (`-- I don't know!` -> `... I don't know!`; `over 9 000!` -> `over 9000!`)
- **OCR**: fixes problems in subtitles introduced by OCR (custom implementation of [SubtitleEdit](https://github.com/SubtitleEdit/subtitleedit)'s dictionaries) (`hands agaInst the waII!` -> `hands against the wall!`)

Hearing Impaired, Common, OCR and Color can be applied automatically on every subtitle downloaded. All mods are manually managable via the channel menu.

Mods are applied on-the-fly, the original content of the subtitle stays available, so mods are completely reversible.

In addition to that Sub-Zero also fixes problems introduced by the subtitle creators themselves - badly changed encodings for example.
Ever had broken music icons in a subtitle? Nordic characters like `Å` which turned into `Ã¥`? Not anymore.

## Installation
Simply go to the Plex Channels in your Plex Media Server, search for Sub-Zero and install it.
For further help or manual installation, [please go to the wiki](https://github.com/pannal/Sub-Zero.bundle/wiki).

## Changelog

2.0.24.1565
- core: fix searchallrecentlymissing task erroring if item not found
- core: fix non-plex-items appearing in and crashing the recently played list
- core: add hybrid-plus activity setting (current media file and next episode)
- podnapisi: fix by using correct guessit parameters

2.0.24.1558
- core: fix handling of broken RAR files from legendas

2.0.24.1555
- core: fix rare microdvd issue from OpenSubtitles by generally providing FPS info when encountering a microdvd subtitle

2.0.24.1549
Changes from 1.4
- wiki: new wiki! (thanks @dane22!)
- core: update subliminal to version 2
- core: update all dependencies
- core: add new providers: legendastv (pt-BR), napiprojekt (pl), shooter (cn), subscenter (heb)
- core: rewritten all subliminal patches for version 2
- core: use SSL again for opensubtitles
- core: improved matching due to subliminal 2 (and SZ custom) tvdb/omdb refiners
- core: improved matching by relying on existing metadata provided by the PMS
- core: improved performance due to multithreaded provider-querying
- core: improved performance due to less physical media file access (no more MKV metadata scanning)
- core: VTT subtitle format output supported (for Chromecast)
- core: rewrote and streamlined internal subtitle data storage format
- core: support Cyrillic and Latin variants of Serbian language
- core: simplified (custom) provider registration; add own provider registry
- core: rewrote recently added missing task
- core: automatically fix badly (re-) encoded unicode entities in subtitles
- core: always store subtitles in proper UTF-8 encoding
- core: add periodic internal subtitle data storage cleanup task
- core: on non-windows systems, utilize a file-based cache database for provider media lists and subliminal refiner results
- core: add manual and automatic subtitle modification framework (fix common OCR issues, remove hearing impaired etc.)
- core: relieve some stress on providers by providing better fine-grained retry handling
- menu: add icons for menu items; update main channel icon
- menu: add subtitle modifications (subtitle content fixes, offset-based shifting, framerate conversion)
- menu: add recently played menu
- menu: add "Get my logs" function to the advanced menu, which zips up all necessary logs suitable for posting in the forums
- menu: add generic "back to season" and "back to series" entries to item detail views to make navigation easier
- config: all scores changed (defaults updated)
- config: remove "Force UTF-8 when storing subtitles" (it's now always implied)
- improve almost everything Sub-Zero did in 1.4 :)

Big thanks to the beta testing team! You know who you are!

[older changes](CHANGELOG.md)


Subtitles provided by [OpenSubtitles.org](http://www.opensubtitles.org/), [Podnapisi.NET](https://www.podnapisi.net/), [TVSubtitles.net](http://www.tvsubtitles.net/), [Addic7ed.com](http://www.addic7ed.com/), [Legendas TV](http://legendas.tv/), [Napi Projekt](http://www.napiprojekt.pl/), [Shooter](http://shooter.cn/), [SubsCenter](http://www.subscenter.org)
