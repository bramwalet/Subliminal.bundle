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
1.4.11.781
- core: cleanup, logging
- core/menu: fix addic7ed display in manual subtitle list
- core: use HTTP for OpenSubtitles instead of HTTPS because of current certificate errors
- core: find better subtitles should now run smoothly even with replaced files (newer parts)


1.4.10.769
- core: hotfix for legacy intent storage regression

1.4.10.768
- core: automatically find better subtitles (configurable)
- menu: display how the subtitle was downloaded (auto, manual, auto-better), in history menu
- menu/core: correctly handle subtitle list for multiple languages
- core: lower minimum series score to list subtitles for to 66
- core: better matching of garbage filenames; we trust Plex now for the series name/movie title fully
- core: add setting to specifically set the file permissions (chmod)


[older changes](CHANGELOG.md)


If you like this, buy me a beer: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG)
