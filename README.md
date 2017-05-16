# Sub-Zero for Plex
[![](https://img.shields.io/github/release/pannal/Sub-Zero.bundle.svg?style=flat)](https://github.com/pannal/Sub-Zero.bundle/releases)
[![master](https://img.shields.io/badge/master-stable-green.svg?maxAge=2592000)]()
[![Maintenance](https://img.shields.io/maintenance/yes/2017.svg)]()

<img src="https://raw.githubusercontent.com/pannal/Sub-Zero.bundle/master/Contents/Resources/subzero.gif" align="left" height="100"> <font size="5"><b>Subtitles done right!</b></font><br />

Checkout **[the Sub-Zero Wiki](https://github.com/pannal/Sub-Zero.bundle/wiki)** by [@ukdtom](https://github.com/ukdtom) <br />
<br style="clear:left;"/>

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
