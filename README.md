# Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat&label=stable)](https://github.com/pannal/Sub-Zero.bundle/releases/latest)<!--[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle/all.svg?maxAge=2592000&label=testing+2.0+RC9)](https://github.com/pannal/Sub-Zero.bundle/releases)--> [![master](https://img.shields.io/badge/master-stable-green.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2018.svg)]()
[![Slack Status](https://szslack.fragstore.net/badge.svg)](https://szslack.fragstore.net)

<img src="https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif" align="left" height="100"> <font size="5"><b>Subtitles done right!</b></font><br />

Check out **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)** by [@ukdtom](https://github.com/ukdtom) and [@mmgoodnow](https://github.com/mmgoodnow) <br />
<br style="clear:left;"/>

If you like this, buy me a beer: <br>[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG) <br>or become a Patreon starting at **1 $ / month** <br><a href="https://www.patreon.com/subzero_plex" target="_blank"><img src="http://www.wenspencer.com/wp-content/uploads/2017/02/patreon-button.png" height="42" /></a> <br>or use the OpenSubtitles Sub-Zero affiliate link to become VIP <br>**10€/year, ad-free subs, 1000 subs/day, no-cache *VIP* server**<br><a href="http://v.ht/osvip" target="_blank"><img src="https://static.opensubtitles.org/gfx/logo.gif" height="50" /></a> 

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
Every subtitle gets a score assigned, based on the matching algorithm. The one with the highest score gets picked automatically. The more information your media filenames have, the better. `Moviename.mkv` has a higher chance of getting bad subtitles than `Moviename.2015.720p.BluRay-RLSGRP`. If you like renaming your media files, you want to have a look at [SZ refiners](https://github.com/pannal/Sub-Zero.bundle/wiki/Refiners).

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
- **Remove Tags**: removes any font style tags from the subtitles (bold, italic, underline, colors, ...)

Hearing Impaired, Common, OCR and Color can be applied automatically on every subtitle downloaded. All mods are manually managable via the channel menu.

Mods are applied on-the-fly, the original content of the subtitle stays available, so mods are completely reversible.

In addition to that Sub-Zero also fixes problems introduced by the subtitle creators themselves - badly changed encodings for example.
Ever had broken music icons in a subtitle? Nordic characters like `Å` which turned into `Ã¥`? Not anymore.

## Installation
Simply go to the Plex Plugins in your Plex Media Server, search for Sub-Zero and install it.
For further help or manual installation, [please go to the wiki](https://github.com/pannal/Sub-Zero.bundle/wiki).

## Big thanks to the beta testing team (in no particular order)!
the.vbm, mmgoodnow, Vertig0ne, thliu78, tattoomees, ostman, count_confucius, 
eherberg, tywilliams_88, Swanny, Jippo, Joost1991 / joost, Marik, Jon, AmbyDK, 
Clay, mmgoodnow, Abenlog, michael, smikwily, shoghicp, Zuikkis, Isilorn, 
Jacob K, Ninjouz, chopeta, fvb

## Changelog

2.5.3.2414

- core: expand user agent list
- core: update subliminal to 4ad5d31
- core: treat 23.976, 23.98, 24.0 fps as equal
- core: correctly skip blacklist entries when iterating through currently known subs
- core: fix unpacking of packs without asked-for-release-group
- core: fix embedded subtitle language detection; add debug log
- core: treat embedded subtitle containing "forced" in its title as forced
- core: improve embedded subtitles detection
- core: store extracted embedded forced subtitles with the "forced" suffix (e.g.: video.en.forced.srt)
- core: don't bother trying to extract embedded subtitle if transcoder wasn't found
- core: fix automatic extraction of unknown embedded subtitle streams
- core: skip immediately searching for new subtitle after successfully extracting embedded
- core: extract embedded ASS: don't transcode to SRT using ffmpeg (Plex Transcoder), do the transcoding later using pysubs2; fixes offset issues
- core: extract embedded: let ffmpeg auto convert mov_text/tx3g to srt
- core: fix transcoder detection; add fallback #460
- core: remove LD_LIBRARY_PATH from environment before calling notification executable
- core: auto extract embedded subtitles in a separate thread
- core: reduce encoding change log spam
- core: only allow one automatic extraction at a time; add optional advanced settings "auto_extract_multithread"
- core: add minimum score a subtitle has to have when considered by the find better subtitles task, when the current subtitle is an extracted embedded one; add advanced_settings entries
- core/config: automatic extraction: add config setting to indicate whether there should be an immediate search for available subtitles after extraction or not (default: off)
- core/menu/submod: add reverse_rtl modification for Hebrew; fixes #409
- core: scoring: assume title match on tvdb_id match
- tasks: search all recently added missing: fix attribute access on missing stored subtitle info
- providers: add hosszupuska (hungarian, thanks morpheus133 for the basic implementation)
- providers: add argenteam (spanish, thanks mmiraglia for the basic implementation)
- providers: addic7ed: use random user agent by default (enforce for existing configs)
- providers: enable subscene by default
- providers: opensubtitles: add fallback for dict based query response in contrast to list/array based
- advanced settings: make text-based-subtitle-formats configurable
- menu: submod: inverse-reverse subtitle timing time-choices for better accessibility
- submod: reduce log spam in case of debug logs enabled
- submod: style tags could result in no output at all
- submod: fix empty content if only non-line-mods were used, no line-mods; fixes #449
- submod: HI: correctly handle style tags when checking for brackets
- submod: HI: don't remove anything that's surrounded by quotes
- submod: HI: double or triple dash is em dash
- submod: HI: HI_before_colon_noncaps, don't assume single quotes are sentence enders
- submod: common: don't uppercase after abbreviations
- submod: common: don't break phone numbers (more than one spaced number pair found)
- submod: common: also count lines only consisting of dots as removable
- submod: common: replace more than 3 consecutive dots with 3 dots
- submod: OCR: "H i." = "Hi."




[older changes](CHANGELOG.md)


Subtitles provided by [OpenSubtitles.org](http://www.opensubtitles.org/), [Podnapisi.NET](https://www.podnapisi.net/), [TVSubtitles.net](http://www.tvsubtitles.net/), [Addic7ed.com](http://www.addic7ed.com/), [Legendas TV](http://legendas.tv/), [Napi Projekt](http://www.napiprojekt.pl/), [Shooter](http://shooter.cn/), [Titlovi](http://titlovi.com), [SubScene](https://subscene.com/)
