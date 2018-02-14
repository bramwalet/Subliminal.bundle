# Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat&label=stable)](https://github.com/pannal/Sub-Zero.bundle/releases/latest)<!--[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle/all.svg?maxAge=2592000&label=testing+2.0+RC9)](https://github.com/pannal/Sub-Zero.bundle/releases)--> [![master](https://img.shields.io/badge/master-stable-green.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2017.svg)]()
[![Slack Status](https://szslack.fragstore.net/badge.svg)](https://szslack.fragstore.net)

<img src="https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif" align="left" height="100"> <font size="5"><b>Subtitles done right!</b></font><br />

Check out **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)** by [@ukdtom](https://github.com/ukdtom) <br />
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
- **Remove Tags**: removes any font style tags from the subtitles (bold, italic, underline, colors, ...)

Hearing Impaired, Common, OCR and Color can be applied automatically on every subtitle downloaded. All mods are manually managable via the channel menu.

Mods are applied on-the-fly, the original content of the subtitle stays available, so mods are completely reversible.

In addition to that Sub-Zero also fixes problems introduced by the subtitle creators themselves - badly changed encodings for example.
Ever had broken music icons in a subtitle? Nordic characters like `Å` which turned into `Ã¥`? Not anymore.

## Installation
Simply go to the Plex Channels in your Plex Media Server, search for Sub-Zero and install it.
For further help or manual installation, [please go to the wiki](https://github.com/pannal/Sub-Zero.bundle/wiki).

## Big thanks to the beta testing team (in no particular order)!
the.vbm, mmgoodnow, Vertig0ne, thliu78, tattoomees, ostman, count_confucius, 
eherberg, tywilliams_88, Swanny, Jippo, Joost1991 / joost, Marik, Jon, AmbyDK, 
Clay, mmgoodnow, Abenlog, michael, smikwily, shoghicp, Zuikkis, Isilorn, 
Jacob K, Ninjouz, chopeta, fvb

## Changelog

2.5.0.2241

- fix issue when removing crap from filenames to not accidentally remove release group #436
- fix initialization of soft ignore list after upgrade fron 2.0


2.5.0.2221

- refiners: add support for retrieving original filename from
 	- drone derivates: sonarr, radarr
 	- filebot
 	- symlinks
    - file_info meta file lists (see wiki)
 
- providers: add subscene (disabled by default to not flood subscene on release)
    - normal search
    - season pack search if season has concluded
 
- core: add provider subtitle-archive/pack cache for retrieving single subtitles from previously downloaded (season-) packs (subscene)
- core/agent: massive performance improvements over 2.0
- core/agent/background-tasks: reduce memory usage to a fraction of 2.0
- core/providers: add dynamic provider throttling when certain events occur (ServiceUnavailable, too many downloads, ...), to lighten the provider-load
- core/agent/config: automatically extract embedded subtitles (and use them if no current subtitle)
- core: fix internal subtitle info storage issues
- core: always store internal subtitle information even if no subtitle was downloaded (fixes SearchAllRecentlyAddedMissing)
- core: fix internal subtitle info storage on windows (gzip handling is broken there)
- core: don't fail on missing logfile paths
- core: fix default encoding order for non-script-serbian
- core: improve logging
- core: add AsRequested to cleanup garbage names
- core: treat SDTV and HDTV the same when searching for subtitles
- core: parse_video: trust PMS season and episode numbers
- core: parse_video: add series year information from PMS if none found
- core: upgrade dependencies
- core: update subliminal to 62cdb3c
- core: add new file based cache mechanism, rendering DBM/memory backends obsolete
- core: treat 23.980 fps as 23.976 and vice-versa
- core: add HTTP proxy support for querying the providers (supports credentials)
- core: only compute file hashes for enabled providers
- core: massive speedup; refine only when needed, exit early otherwise
- core: store last modified timestamp in subtitle info storage
- core: only write to subtitle info storage if we haven't had one or any subtitle was downloaded
- core: only clean up the sub-folder if a subtitle-sub-folder has been selected, and not the parent one also
- core: support for CP437 encoded filenames in ZIP-Archives
- core: use scandir library instead of os.listdir if possible, reducing performance-impact
- core: archives: support multi-episode subtitles (partly)
- core: subtitle cleanup: add support for hi, cc, sdh secondary filename tags; don't autoclean .txt
- core: increase request timeout by three times in case a proxy is being used
- core: fix language=Unknown in Plex when "Restrict to one language"-setting is set
- core: refining: re-add old detected title as alternative title after re-refining with plex metadata's title; fixes #428
- core: implement advanced_settings.json (see advanced_settings.json.template for reference, copy to "Plug-in Support/Data/com.plexapp.agents.subzero" to use it)
- core/tasks: fix search all recently added missing (the total number of items will change in the menu while running), reduces memory usage
- core/menu: add support for extracting embedded subtitles using the builtin plex transcoder
- core/menu: skip wrong season or episode in returned subtitle results
- core/config: fix language handling if treat undefined as first language is set
- providers: remove shooter.cn
- providers: add support for zip/rar archives containing more than one subtitle file
- submod: common: remove redundant interpunction ("Hello !!!" -> "Hello!")
- submod: skip provider hashing when applying mods
- submod: correctly drop empty line (fixing broken display)
- submod: OCR: fix F'xxxxx -> Fxxxxx
- submod: HI: improve bracket matching
- submod: OCR: fix l/L instead of I more aggressively
- submod: common: fix uppercase I's in lowercase words more aggressively
- submod: HI: improve HI_before_colon
- submod: common: be more aggressive when fixing numbers; correctly space out spaced ellipses; don't break spaced ellipses; handle multiple spaces in numbers
- menu: add support for extracting embedded subtitles for a whole season
- menu: add reapply mods to current subtitle
- menu: pad titles for more submenus, resulting in detail view in PlexWeb
- menu: add subtitle selection submenu (if multiple subtitles are inside the subtitle info storage; e.g. previously downloaded ones or extracted embedded)
- menu: advanced: add skip findbettersubtitles menu item, which sets the last_run to now (for debugging purposes)
- menu: ignore: add more natural title for seasons and episodes (kills your old ignore lists!)
- config: skip provider hashing on low impact mode
- config: add limit by air date setting to consider for FindBetterSubtitles task (default: 1 year)
- advanced settings: define enabled-for media types per provider
- advanced settings: define enabled-for languages per provider
- advanced settings: add deep-clean option (clean up the subtitle-sub-folder and the parent one)


[older changes](CHANGELOG.md)


Subtitles provided by [OpenSubtitles.org](http://www.opensubtitles.org/), [Podnapisi.NET](https://www.podnapisi.net/), [TVSubtitles.net](http://www.tvsubtitles.net/), [Addic7ed.com](http://www.addic7ed.com/), [Legendas TV](http://legendas.tv/), [Napi Projekt](http://www.napiprojekt.pl/), [Shooter](http://shooter.cn/), [Titlovi](http://titlovi.com), [SubScene](https://subscene.com/)
