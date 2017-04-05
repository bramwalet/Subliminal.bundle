# Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat)](https://github.com/pannal/Sub-Zero.bundle/releases)
[![master](https://img.shields.io/badge/master-stable-green.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2017.svg)]()

<img src="https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif" align="left" height="100"> <font size="5"><b>Subtitles done right!</b></font><br />

Checkout **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)** by [@ukdtom](https://github.com/ukdtom) <br />
<br style="clear:left;"/>

## Changelog

1.4.27.967
- core: remember the last 10 played items; only consider on_playback for "playing" state within the first 60 seconds of an item


1.4.27.965
- core: on_playback activity bugfixes


1.4.27.957
- core: correctly fall back to the next best subtitle if the current one couldn't be downloaded; hopefully fixes #231
- core: add "Scan: which external subtitles should be picked up?"-setting
- core: add optional on_playing activities. refresh currently playing movie, refresh next episode in season, both or none; fixes #259 #33
- core: skip to next best subtitle if findbettersubtitles failed
- core: add setting to treat undefined-language embedded subtitle as configured language1 #239
- core: fix handling of inexistant addic7ed show id
- core: fix regression issue breaking relative custom subtitle folder handling
- core: fix loading of stored subtitle info data of now-non-existant items
- core: re-add separate global subtitle folder handling
- menu: remove obsolete actions from the advanced menu


[older changes](CHANGELOG.md)


If you like this, buy me a beer: [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=G9VKR2B8PMNKG)
