#Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat)](https://github.com/pannal/Sub-Zero.bundle/releases)
[![master](https://img.shields.io/badge/master-stable-green.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2016.svg?maxAge=2592000)]()

![logo](https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif)

##### Subtitles done right

## Information
I've been receiving great support by [@ukdtom](https://github.com/ukdtom) recently:<br/>
He has created **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)**. Please have a look in case of any questions.

## Changelog

1.4.16.822
- menu: add per-section recently added menu
- menu: fix accidentally double-triggering a just triggered force-refresh
- core: reorder settings in a more logical, grouped way
- core: add simple automatic filesystem/external leftover subtitle cleaning (#133, #152)
- core: fix force-refresh for big seasons/series
- core: add setting to look for forced/foreign-only subtitles only (only works for opensubtitles and podnapisi)
- core: fix custom subtitle folder was being ignored (#211)
- core: only trust PMS for its movie name, not the series title (fixes #210)
- core: full support (in filesystem/external mode) for forced/default/normal subtitle tags
- core: ignore "non-standard" external subtitle files when scanning by default (everything but .srt, .ass, .ssa, fixes #192)
- core: lower default max_recent_items_per_library to 500
- core: skip forced/foreign-only subtitles if not specifically wanted
- core: modify the task queue, hopefully helping #206
- core: update anonymous usage collection

1.4.11.781
- core: cleanup, logging
- core/menu: fix addic7ed display in manual subtitle list
- core: use HTTP for OpenSubtitles instead of HTTPS because of current certificate errors
- core: find better subtitles should now run smoothly even with replaced files (newer parts)


[older changes](CHANGELOG.md)


If you like this, buy me a beer: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG)
