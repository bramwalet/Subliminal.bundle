# Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat&label=stable)](https://github.com/pannal/Sub-Zero.bundle/releases/latest)<!--[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle/all.svg?maxAge=2592000&label=testing+2.0+RC9)](https://github.com/pannal/Sub-Zero.bundle/releases)--> [![master](https://img.shields.io/badge/master-stable-green.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2018.svg)]()
[![Slack Status](https://szslack.fragstore.net/badge.svg)](https://szslack.fragstore.net)

<img src="https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif" align="left" height="100"> <font size="5"><b>Subtitles done right!</b></font><br />

Check out **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)** by [@ukdtom](https://github.com/ukdtom) and [@mmgoodnow](https://github.com/mmgoodnow) <br />
<br style="clear:left;"/>

<br />

---

**[The future of Sub-Zero](https://www.reddit.com/r/PleX/comments/9n9qjl/subzero_the_future/)**

---

If you like this, buy me a beer: <br>[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG) <br>or become a Patreon starting at **1 $ / month** <br><a href="https://www.patreon.com/subzero_plex" target="_blank"><img src="http://www.wenspencer.com/wp-content/uploads/2017/02/patreon-button.png" height="42" /></a> <br>or use the OpenSubtitles Sub-Zero affiliate link to become VIP <br>**10€/year, ad-free subs, 1000 subs/day, no-cache *VIP* server**<br><a href="http://v.ht/osvip" target="_blank"><img src="https://static.opensubtitles.org/gfx/logo.gif" height="50" /></a> 

## Introduction
#### What's Sub-Zero?
Sub-Zero is a metadata agent and interface-plugin at the same time, for the popular Plex Media Server environment.

#### Why not use the builtin OpenSubtitles agent?
Because it doesn't deliver. Especially for very new media items it may pick up none or bad subtitles for your media. Also it doesn't know when "better" subtitles get released for your media file.

*Mostly all of the key-features listed below don't apply to the default OpenSubtitles subtitle agent in Plex.*

## Key-Features
This is just a tiny peek at the full feature-set of Sub-Zero.

#### Searching/Matching
It searches up to 10 individual subtitle provider sites and APIs, selects the best matching subtitle and downloads it for you.

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

#### Interface
The automatic matching Sub-Zero does has been improved massively over the last years and reaches an extremely high accuracy for recently-released items, in the first 6 hours. It still might be, that you want some manual managability over your library and its subtitles. This is where the interface comes into play.

It allows you to trigger background tasks, browse your library based on several different starting points, adds a recently-viewed menu for instant access to your recently played media and allows you to list and select available subtitles for any item in your library.

#### Modification and Fixing
With Sub-Zero 2.0 automatic and manual subtitle modifications have been included.
They currently consist of six individual mods:
- **Offset**: Your subtitle is out of sync? Manually adjust the timing of your subtitles
- **FPS**: Your subtitle is getting slower over time, or faster over time? Maybe the framerate is wrong. The FPS mod can fix that.
- **Hearing Impaired**: Removes HI-tags from subtitles (such as `(SIRENS WAIL)`, `DOCTOR: Rose!`)
- **Color**: Adds color to your subtitles (for playback devices/software that don't ship their own color modes; only works for players that support color tags)
- **Common**: Fixes common issues in subtitles, such as punctuation (`-- I don't know!` -> `... I don't know!`; `over 9 000!` -> `over 9000!`)
- **OCR**: Fixes problems in subtitles introduced by OCR (custom implementation of [SubtitleEdit](https://github.com/SubtitleEdit/subtitleedit)'s dictionaries) (`hands agaInst the waII!` -> `hands against the wall!`)
- **Remove Tags**: Removes any font style tags from the subtitles (bold, italic, underline, colors, ...)
- **Reverse RTL**: Reverses the punctuation in right-to-left subtitles for problematic playback devices
- **Fix Uppercase**: Tries to make subtitles that are completely uppercase readable

Hearing Impaired, Common, OCR, Fix Uppercase, Reverse RTL and Color can be applied automatically on every subtitle downloaded. All mods are manually managable via the interface.

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
Jacob K, Ninjouz, chopeta, fvb, Jose

## Changelog

2.6.4.2834
- core: add option to use custom (Google, Cloudflare) DNS to resolve provider hosts in problematic countries; fixes #547
- core: add support for downloading subtitles only when the audio streams don't match (any?) configured languages; fixes #519
- core: add support for an include list instead of an ignore list; add the option to disable SZ by default, then enable it per item/series/section (inverse ignore list)
- core/menu/config: support forced/foreign subtitles independently
- core: fallback for OSError on scandir, should fix #532
- core: add config versioning/migration system
- core: correctly force non-foreign-only-capable providers off; remove subscene from foreign-only capable providers
- core: scanning: collect information about audio streams
- core: use correct storage path when storing subtitle info, when only VTT is used
- core: fix disabled channel mode
- core/menu: extract embedded: add extracted embedded subtitles to history
- core: embedded subtitle streams: don't try parsing the language if inexistant
- core: subtitle: fix log call, fixes #569
- core: download best subtitles: only use actually languages searched for
- core: refiners: tvdb: warn instead of error when no matching series was found
- core: scanning: re-add expected title to guessit for narrowing down the video title
- core: resolve #583
- core: archives: explicitly skip forced subtitles if not searched for, when picking from an archive
- core: activities/auto-refresh: fix hybrid-plus for movies
- core: don't disable plugin if all providers throttled; fix #585 #574
- core: skip cleanup for ignored paths
- core: update requests to 2.20.0 (fixes security issue)
- core: update certifi to 2018.10.15
- core: auto extract: don't overwrite local sub even if unknown to SZ
- config: set autoclean leftover/unused to off by default
- providers: opensubtitles: respect rate limit (40 hits/10s); should fix long throttling behaviour
- providers: opensubtitles: handle bad/inexistant responses
- providers: opensubtitles: log bad response data
- providers: opensubtitles: treat empty response as ServiceUnavailable for now
- providers: opensubtitles: log reason for ServiceUnavailable
- providers: legendastv: match second title and imdb id
- providers: titlovi: fix language handling (thanks @viking1304)
- providers: titlovi: proper handling of archives with both cyrlic and latin subtitles (thanks @viking1304) 
- providers: titlovi: allow direct subtitle downloads as fallback (when a subtitle, not an archive was returned)
- providers: hosszupuska: implement site change (thanks @morpheus133)
- providers: supersubtitles: add base properties to subtitle
- providers: opensubtitles, podnapisi: fix foreign/forced handling
- providers: subscene: use original/sceneName if possible
- menu: fix plugin not responding when ignoring an item in certain menus; fixes #535
- menu: select active subtitle: return to item details afterwards; correctly set current
- menu: add item thumbnails to history and a couple of submenus
- menu: history: use series thumbnail instead of episode screenshot
- menu: add full soft include/exclude menu handling
- menu: add support for separate forced and not-forced subtitles
- menu: fix order of embedded subtitle streams in item detail
- menu: support S00E00 and equivalent
- submod: add option to fix only-uppercase subtitles and make them readable
- submod: keep track of actually applied mods
- submod: correctly merge mods of the same kind (offset)
- submod: OCR: add dictionaries for bosnian and norwegian bokmal; update dicts for dan, eng, hrv, spa, srp, swe
- submod: OCR/HI: skip certain processors for all-caps subs
- submod: HI: only remove caps before colon if the colon is followed by whitespace or EOL; fixes #542
- submod: HI: remove MAN:
- submod: common: improve detection and normalization of quotes, apostrophes
- submod: common: fix double quotes that are meant to be single quotes inside words
- submod: common: normalize small hyphens to dash
- submod: common: remove line only consisting of colon; remove empty colon at start of line
- submod: common: add space after punctuation
- submod: common: fix lowercase i for english language
- submod: common: better fix for music symbols
- submod: reverse_RTL: also reverse ":,'-" chars in CM_RTL_reverse (thanks @doopler)
- submod: reverse_RTL: enable mod for arabic, farsi and persian besides hebrew
- i18n: fix not used translation for recently added missing subtitles menu
- i18n: fix spanish translation, fixes #543
- i18n: Hungarian translation is incomplete




[older changes](CHANGELOG.md)


Subtitles provided by [OpenSubtitles.org](http://www.opensubtitles.org/), [Podnapisi.NET](https://www.podnapisi.net/), [TVSubtitles.net](http://www.tvsubtitles.net/), [Addic7ed.com](http://www.addic7ed.com/), [Legendas TV](http://legendas.tv/), [Napi Projekt](http://www.napiprojekt.pl/), [Shooter](http://shooter.cn/), [Titlovi](http://titlovi.com), [aRGENTeaM](http://argenteam.net), [SubScene](https://subscene.com/), [Hosszupuska](http://hosszupuskasub.com/)

[3rd party licenses](https://github.com/pannal/Sub-Zero.bundle/tree/master/Licenses)
