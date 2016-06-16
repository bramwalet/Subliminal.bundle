#Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat)](https://github.com/pannal/Sub-Zero.bundle/releases)
[![master](https://img.shields.io/badge/master-unstable-red.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2016.svg?maxAge=2592000)]()

![logo](https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif)

##### Subtitles done right

## Information
I've been receiving great support by [@ukdtom](https://github.com/ukdtom) recently:<br/>
He has created **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)**. Please have a look in case of any questions.

## Changelog

1.3.46.606
- core: hotfix for new users (who've never downloaded a subtitle with SZ before); fixes #169


1.3.46.605

- add wiki (thanks @ukdtom / @dane22)
- core: remove necessity of Plex credentials; fixes #148
- core: fix non-SRT subtitle support; fixes #138
- core: generic source overhaul in preparation for release 1.4
- core: better filesystem encoding detection; may fix #159
- core: add encoding handling for windows-1250 and windows-1251 encoding (eastern europe); fixes #162
- core: overhaul ignore handling; fixes #164
- core: implement ignore by path setting; fixes #134
- core: add setting for optional fallback to metadata storage, if filesystem storage failed; fixes #100
- core: add setting for notifying an executable after a subtitle has been downloaded (see Wiki); fixes #65
- core: only handle sections for which Sub-Zero is enabled (in PMS agent settings); fixes #167
- menu: add series/season force-refresh
- menu: show item thumbnail/art where applicable
- menu: mitigate PlexWeb behaviour of calling our handlers twice; fixes #168

[older changes](CHANGELOG.md)


If you like this, buy me a beer: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG)
