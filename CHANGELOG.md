2.0.26.1695
## ATTENTION: THIS RELEASE RESETS YOUR CONFIGURED LANGUAGES TO DEFAULT!
- core: fix bug that caused SZ not to work for Windows users with special characters in their username
- core: fix issues when logging failed manual download actions
- core: update guessit to 2.1.4
- core: fix issue causing the background task scheduler to stop after changing preferences
- core: fix polish encoding (try windows-1250 first, then iso 8859-2)
- core: remove subscenter provider as it now uses captchas
- core: add titlovi as default provider (thanks viking!)
- core: increase default PMS API request timeout to 15 (old: 10, max: 45); add preference for that
- core: re-add separate legacy FindMissingSubtitles task and run it on the first run to prime SZ's internal subtitle storage
- core: add "low impact mode" for people with remote filesystems (currently enabled for List LANGUAGE subtitles in detail menu); alleviates certain plexweb timeout issues
- menu: change naming of find missing subtitles menu item
- legendastv: fix multi value guessit issues
- submod: OCR: update eng and hrv OCR replace dictionaries; fix ". L am huge"


2.0.25.1635
- core: update memory handling, possibly reduce memory problems of 2.0
- core: support for MPL2 subtitle format
- core: update task handling
- core: re-enable NVIDIA SHIELD support by fixing rarfile behaviour
- core: add SZ_UNRAR_TOOL environment variable for custom unrar location
- core: disable SZ when no providers are enabled
- core: only start activity monitor if channel or agent are enabled
- core: improve custom provider integration
- core: update eastern european encoding detection (especially Romanian)
- tasks: reduce provider stress by introducing wait times between searches/downloads
- windows: correctly ship UnRAR.exe
- windows: skip DBM checks
- addic7ed: fix Nip/Tuck
- subscenter: use new domain


2.0.24.1581
- legendastv: ship unrar.exe for Windows users (fixes unrar issues)
- addic7ed: fix TooManyRequests error
- submod: OCR fixes NL: add custom dictionary data for malformed characters
- submod: OCR fixes: update hrv/NL dictionaries
- submod: common: remove spaces before punctuation
- podnapisi: now returns more subtitles again
ATTENTION: Sub-Zero is still broken on PMS for SHIELD. Help needed!


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


2.0.23.1464 RC10.1
 - core: huge bugfix; please check `Library/Application Support/Plex Media\ Server/Plug-in Support/Data/com.plexapp.agents.subzero/DataItems`
         for any `subs_XXXXX.json.gz` file bigger than 500kb and delete them


2.0.23.1456 RC10
- core: findBetterSubtitles: increase series cutoff by 2 (resolution match)
- core: add VTT format
- core: fix crashes regarding DBM/cache management
- core: update rarfile.py
- core: add missing encodings
- core: full support for Serbian subtitles (Cyrillic and Latin)
- podnapisi: fix pt-BR, srp-cyrl and srp-latn
- core: implement own provider registry and ditch the subliminal one
- core: use ftfy library to fix re-encoding errors inside subtitles introduced by the subtitle author
- core: always store and save subtitles normalized to UTF-8
- core: replace spaced dashes in movie/series names before re-refining with plex metadata info
- submod: remove_HI: handle multiline brackets correctly


2.0.20.1364 RC9
- core: performance improvements
- core: if info couldn't be guessed from the filename, fill missing info from PMS #270
- submod: OCR: add more to the eng dictionary
- submod: HI: fixed some issues with font style tags
- core: don't ignore subtitles from providers that don't have hearing impaired info, when hearing impaired mode is set to "force non-HI"
- legendastv/menu: fix manual subtitle selection issues in menu
- core: improve specials matching on OpenSubtitles
- core: update guessit


2.0.19.1337 RC8
- napiprojekt: fixed: couldn't convert microdvd to SRT in certain occasions
- core: when normalize to UTF-8 is enabled, also store the subtitle in UTF-8 encoding in the internal storage
- core: add more encodings for western/eastern/northern europe
- submod: OCR: update dictionaries from SubtitleEdit
- submod: common: be smarter about uppercase i's in words that should have lowercase L's
- submod: fix unopened/unclosed font style tags after modification
- core: re-enable OMDB support
- core: update guessit for better matching
- core: fix SearchAllRecentlyMissing (was broken since RC3)


2.0.19.1299 RC7
- submod: offset mods now get merged internally when applied multiple times (to avoid errors and increase performance)
- submod: improve performance
- submod: core mods (OCR, common, remove_HI) now are always applied in a fixed order internally, regardless of the order they were added in
- submod: CM_spaces_in_numbers: don't break up ellipses (30... 29... 28...)
- submod: CM_spaces_in_numbers: don't fix countdown numbers (30, 29, 28)
- submod: remove_HI: make bracket removal more aggressive
- submod: remove_HI: be less aggressive when removing text-before-colon
- submod: remove_HI: remove all-uppercase-before-sentence (THIS IS ALL UPPERCASE And here starts a sentence -> And here starts a sentence)
- submod: fix all character ranges to include non-ASCII characters
- add new README for 2.0


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


1.4.23.920
- core: handle undecodable paths better #255
- core: don't fail on unrecoverable data #257
- core: increase default scores from 110 (series) and 23 (movies) to 116 and 33
- core: fix global subtitle folder handling #234
- core: better invoking of configured executable after subtitle addition #247


1.4.22.908
- core: hotfix for more robust migrations


1.4.22.898
- core: migrate history and subtitle storage to a better implementation, making it far more stable. subtitle storage now also stores the downloaded subtitle data for future usage, so it will be possible to switch between them
- core/menu: manual subtitle download and the FindBetterSubtitles-task now also work with metadata storage (hi @ shield users)
- core: optimize FindBetterSubtitles-task


1.4.19.882
- core: fix tasks for new users
- core: double check pin correctness/existance when pin is enabled


1.4.19.878
- core/menu: fix a task's last runtime display
- core: task optimizations
- core: fix leftover subtitles cleanup handling in case of a custom subtitle folder #234
- core: run the scheduler even if permissions for libraries are wrong ("fixes" #236)
- core: store subtitle history data in a different data format; reduce used storage size drastically (#233)


1.4.19.866
- core: fix wrong usage of LogKit


1.4.19.857

- core: add option to enable/disable channel and/or agent modes (fixes #220)
- core: skip inexistent internal streams when scanning for internal subtitles (fixes #222)
- core: fix filename encoding (fixes #223)
- core: storage optimizations
- menu: add pin-based channel menu locking (the whole channel or only the advanced menu)


1.4.17.836
- core: support for any media file that PMS supports (internal subtitles on mp4 for example)
- core: fix broken ignore folders containing "subzero.ignore/.subzero.ignore/.nosz"
- core: fix duplicate subtitles (lowercase/default case)
- core: fix broken tasks queue due to oversight


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


1.4.10.769
- core: hotfix for legacy intent storage regression

1.4.10.768
- core: automatically find better subtitles (configurable)
- menu: display how the subtitle was downloaded (auto, manual, auto-better), in history menu
- menu/core: correctly handle subtitle list for multiple languages
- core: lower minimum series score to list subtitles for to 66
- core: better matching of garbage filenames; we trust Plex now for the series name/movie title fully
- core: add setting to specifically set the file permissions (chmod)


1.4.5.742
- core: fix force-refresh in certain situations
- menu: add history
- menu: add manual subtitle selection
- menu: run Items with missing subtitles in separate thread for big libraries
- settings: add history list size option (default: 100)
- settings: add new default scores (TV: 110); use input instead of dropdown
- settings: increase default missing subtitles amount per library to 2000
- core: generic rewrites and optimizations
- core: better hash verification
- core: add anonymous usage data (opt-out in settings)
- core: fix pt-BR display (IETF) again
- wiki: update (thanks @dane22!) - quick URL: http://v.ht/szwiki
- wiki: add score explanation - quick URL: http://v.ht/szscores
- core: add persian/farsi encoding support


1.3.49.636
- core/menu: fix force refreshing (again)
- core/menu: fix redundant route calls


1.3.49.630 (backported some changes of the develop-1.4 branch to 1.3)
- core/menu: make addic7ed boost configurable; lower the default boost value massively (to 10)
- core: fix force refreshing (hopefully)
- core: add (thai) tis-620 subtitle encoding support
- menu: lower letter based menu browsing from 200 to 80 items
- core: support greek encodings (windows-1253, cp1253, cp737, iso8859_7, cp875, cp869, iso2022_jp_2, mac_greek); hopefully fixes badly saved greek subs
- menu: add generic back-to-home button to the top of every container view
- menu: warn the user when SZ isn't enabled for any sections/libraries
- menu: always re-check permissions status and enabled sections when opening the main menu; no server restart necessary anymore


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


1.3.33.522

- core: fix library permission detection on windows; fixes #151
- core: "Restrict to one language" now behaves like it should (one found subtitle of any language is treated as sufficient); fixes #149
- core: add support for other subtitle formats such as ssa/ass/microdvd, convert to srt; fixes #138
- core: hopefully more consistent force-refresh handling (intent); fixes #118


1.3.31.513

- core: add option to only download one language again (and skip the addition of .lang to the subtitle filename) (default: off); fixes #126 
- core: add option to always encode saved subtitles to UTF-8 (default: on); fixes #128
- core: add fallback encoding detection using bs4.UnicodeDammit; hopefully fixes #101
- core: update libraries: chardet, beautifulsoup, six
- menu/core: check Plex libraries for permission problems on plugin start and report them in the channel menu (option, default: on); fixes #143
- menu: while a manual refresh takes place, add a refresh button to the top of the SZ menu for convenience
- menu: move the "add/remove X to ignore list" menu item to the bottom of the list on item detail 


1.3.27.491

- menu/core: make Sub-Zero channel menu optional (setting: "Enable Sub-Zero channel (disabling doesn't affect the subtitle features)?")
- OpenSubtitles: detect and match video/subtitle FPS (framerate) to reduce out of sync subtitle matches
- core: internal fixes; add _markerlib library (rare)
- core: don't score tvshow episode title matches, should improve episode subtitle matches quite a bit (and reduce out of sync subtitles)
- OpenSubtitles: make tag/exact filename matches optional (setting: "I keep the exact (release-) filename of my media files")
- menu: unicode video title errors fixed
- TVSubtitles: correctly match certain show IDs (such as "Series Name (US)")
- core: don't break subtitle evaluation on crashed guessing


1.3.23.459

- core: slight code cleanup and fixes
- core: add physical (filesystem) ignore mode (create files named `subzero.ignore`, `.subzero.ignore`, `.nosz` to ignore specific files/seasons/series/libraries)
- core: fix guessit hinting of tv series with rare folder layout (e.g. series_name/a/S01E01.mkv)
- core: remove "format" necessity from (opensubtitles) hash-validation
- OpenSubtitles: dramatically improve matching: add tag (exact filename) matching and treat it just like hash matches
- core: ignore embedded forced subtitles (fixes #106)
- docs: update
- settings: clarify


1.3.20.422  
- tvsubtitles: show matching was partially broken
- addic7ed: better show matching
- core: correctly skip subtitles stored in filesystem if metadata storage was selected (Local Media Assets agent may still pick them up)  
- core: fix local API access (switch from HTTPS to HTTP)
- core: fix handling of library names and media paths with non-ascii chars in it  
- core: fix bundle version to correctly display current bundle version
- core: skip downloading multi-CD subtitle
- settings: clarify


1.3.20.403
- core: handle & and - ("and" and dash) in names
- core: fixed handling of internal metadata subtitles
- re-upped the minimum tv score to 85 (may be even higher in the future)
- opensubtitles: possibly significantly better movie matching (now also query for movie title, instead of only querying for video hash)


1.3.20.396
- core: fix logging handlers (when saving log_level settings loggers got duplicated)
- core: better movie matching by only hinting the filename and the last subdirectory to guessit (instead of the full path)
- core: don't fail on wrong detection/scanning of media file
- lower minimum tv series score from 85 to 67 (removed title; composed of: series=44 + season=11 + episode=11 + hearing_impaired=1)


1.3.19.379
- core: new recent items implementation (used in "Items with missing subtitles"), now really picking up everything instead of using Plex's recently_added API endpoint
- core: be more strict about title matching - a matched title doesn't automatically mean season and episode are correct, too
- core: rewrote the hash matching algorithm to not blindly trust hash matches anymore, but instead episodes have to match the series name, season number, episode number and format (BluRay, HDTV...); movie have to at least match the title, format and codec for the hash to be considered
- core: remove TheSubDB support for now, as it only supports hash-based matching
- scheduler: more robust item-fail-handling (fixes #81)
- config: "Scan: include embedded subtitles" now by default is off, as embedded subs have proven to be pretty unreliable
- config: add configuration option for how many items per library are to be considered recent (default: 200)
- config: make logging verbosity configurable, default: WARNING - log files should be considerably smaller now
- config: make console logging optional, default: off - good for development/debugging
- config: removed the ignore lists
- menu: added "Browse all items", where you can browse all your libraries and manage your ignore list (add/remove sections/series/items)
- menu: added "Display ignore list", where you can manage your ignored sections, series and items
- menu: the submenu titles are now dynamically composed of a breadcrumb-style tree so you see where you are
- menu: show the current and past state of the important menu actions such as (force)-refresh an item or refreshing the menu, on the Refresh-button's description
- plugin now isn't in the dev mode by default and has logging to the console off (in certain configurations this resulted in huge syslogs)


1.3.6.316
- scheduler: missing subtitles task now able to handle huge libraries (thanks @chopeta, @comrade)
- scheduler: detect item-stalling, add wait and retry logic to make missing subtitles task more robust
- scheduler: report failed items to logs after task run completion
- hint series name and episode title, or movie title to guessit to make detection way better (e.g. for Mr. Robot)

1.3.6.304
- scheduler: correct the recent-determination of the search for missing subtitles in recently_added task
- scheduler: rewrote search for missing subtitles task; it now requests refreshes one by one and not in bulk anymore (hopefully fixes stalling)
- handle rare cases of weird file system encodings (ANSI_X3.4-1968 for example)
- fix simplejson warning on startup

1.3.6.297
- rename Sub-Zero to Sub-Zero.bundle (requirement for adding Sub-Zero to the Plex channel directory)
- channel: add logging actions for the internal storage to the advanced menu
- channel: handle item titles with foreign characters in them correctly
- (hopefully) fix handling file names with foreign characters in them when scanning for local media
- reformat the whole project, mostly honoring pep8
- scheduler: fixed some serious bugs; broken tasks (stalled) and some errors many of you have seen should be gone now
- scheduler: partly rewritten to be more robust, again
- settings: move Plex.tv credentials to the top

1.3.5.281
- fix tasks broken for 1.2 -> 1.3.5 upgraders

1.3.5.273 (same build as Beta Release 1.3.0.273) - changes from previous stable 1.2.11.180
- add a channel menu, making this plugin a hybrid (Agent+Channel)
- add a generic background task scheduler
- add a task to search for subtitles for items with missing subtitles (manually triggered and automatic)
- add artwork
- add Plex.tv credentials/token-generation support (needed for Plex Home users for the API to work)
- addic7ed: improve show name matching again
- channel: able to browse current on-deck and recently-added items, and refresh or force-refresh (search for new subtitles) single items
- add library/series/video blacklist for items which should be skipped in "Search for missing subtitles"-task
- add donation links
- change the license to The Unlicense (while keeping the original MIT license from subliminal.bundle intact)
- store subtitle information in internal plugin storage (for later usage)
- many internal code improvements
- update documentation

1.3.0.273
- more robust update functionality
- menu: add refresh button to menu (to see the task state updating)
- scheduler: actually skip a task if it's already running
- scheduler: better behaviour when a task is running and a single item is refreshed at the same time
- menu: enforce ascii on item titles

1.3.0.261
- removed localization again

1.3.0.259
- forgot locale-data

1.3.0.256
- fix force-refresh single items to actually force-refresh
- re-add babel library

1.3.0.253
- rewrote background tasks subsystem
- keep track of the status of a task and its runtime
- add task state in channel menu to "Search for missing subtitles"
- add date/time localization to channel menu
- hide plex token from logs, when requesting
- fix addic7ed show id parsing for shows with year set
- test PMS API connectivity and fail miserably if needed (channel disabled, scheduler disabled)
- feature-freeze for 1.3.0 final

1.3.0.245
- add the option to buy me a beer
- clarify menu items
- more robust scheduler handling (should fix the issues of scheduler runs in the past)
- internal cleanups
- add date_added to stored subtitle info (all of the 1.3.0 testers: please delete your internal subtitle storage using the channel->advanced menu)

1.3.0.232
- integrate plex.tv authentication for plex home users (test phase)
- menu cleanup
- more info in the menu (scheduler last and next run for example)
- hopefully fixed intent handling (should throw less errors now)
- fix version display in agent names

1.3.0.222
- bugfix for search missing subtitles
- schedduler: honor "never"

1.3.0.216
- add channel menu
- add generic task scheduler
- add functionality to search for missing subtitles (via recently added items)
- add artwork
- change license to The Unlicense
- ...

1.2.11.180
- fix #49 (metadata storage didn't work)
- add better detection for existing subtitles stored in metadata

1.2.11.177
- updated naming scheme to reflect rewrite.major.minor.build (this release is the same as 1.1.0.5)

1.1.0.5
- addic7ed: fixed error in show id search
- addic7ed: even better show matching
- adjusted default scores: TV: 85, movies: 23
- add support for com.plexapp.agents.xbmcnfo/xbmcnfotv (proposed to the author [here](https://github.com/gboudreau/XBMCnfoMoviesImporter.bundle/pull/63) and [here](https://github.com/gboudreau/XBMCnfoTVImporter.bundle/pull/70))

1.1.0.3
- addic7ed/tvsubtitles: be way smarter about punctuation in series names (*A.G.E.N.T.S. ...*)
- ditch LocalMediaExtended and incorporate the functionality in Sub-Zero (**RC-users: delete LocalMediaExtended.bundle and re-enable LocalMedia!**)
- remove (unused) setting "Restrict to one language"
- add "Treat IETF language tags as ISO 639-1 (e.g. pt-BR = pt)" setting (default: true)
- change default external storage to "current folder" instead of "/subs"
- adjust default scores

RC-5.2
- revert back to /plexinc-agents/LocalMedia.bundle/tree/dist instead of /plexinc-agents/LocalMedia.bundle/tree/master, as the current public PMS version is too old for that

RC-5.1
- make hearing_impaired option more configurable and clear (see #configuration-)

RC-5
- fix wrong video type matching by hinting video type to guessit
- update to newest LocalMediaExtended.bundle (incorporated plex-inc's changes)
- show page links for subtitles in log file instead of subtitle ID
- add custom language setting in addition to the three hardcoded ones
- if a subtitle doesn't match our hearing_impaired setting, ignore it
- add an optional boost for addic7ed subtitles, if their series, season, episode, year, and format (e.g. WEB-DL) matches

RC-4
- rename project to Sub-Zero
- incorporate LocalMediaExtended.bundle
- making this a multi-bundle plugin
- update default scores
- add icon

RC-3
- addic7ed/tvsubtitles: punctuation fixes (correctly get show ids for series like "Mr. Poopster" now)
- podnapisi: fix logging
- opensubtitles: add login credentials (for VIPs)
- add retry functionality to retry failed subtitle downloads, including configurable amount of retries until discarding of provider
- move possibly not needed setting "Restrict to one language" to the bottom
- more detailed logging
- some cleanup

RC-2
- fix empty custom subtitle folder creation
- fix detection of existing embedded subtitles (switch to https://github.com/tonswieb/enzyme)
- better logging
- set default TV score to 15; movie score to 30

RC-1
- fix subliminal's logging error on min_score not met (fixes #15)
- separated tv and movies subtitle scores settings (fixes #16)
- add option to save only one subtitle per video (skipping the ".lang." naming scheme plex supports) (fixes #3)

beta5
- fix storing subtitles besides the actual video file, not subfolder (fixes #14)
- "custom folder" setting now always used if given (properly overrides "subtitle folder" setting)
- also scan (custom) given subtitle folders for existing subtitles instead of redownloading them on every refresh (fixes #9, #2)

beta4
- ~~increased score of addic7ed subtitles a bit~~ (not existing currently)
- **support for newest Subliminal ([1.0.1](27a6e51cd36ffb2910cd9a7add6d797a2c6469b7)) and guessit ([0.11.0](2814f57e8999dcc31575619f076c0c1a63ce78f2))**
- **plugin now also [works with com.plexapp.agents.thetvdbdvdorder](924470d2c0db3a71529278bce4b7247eaf2f85b8)**
- providers fixed for subliminal 1.0.1 ([at least addic7ed](131504e7eed8b3400c457fbe49beea3b115bc916))
- providers [don't simply fail and get excluded on non-detected language](1a779020792e0201ad689eefbf5a126155e89c97)
- support for addic7ed languages: [French (Canadian)](b11a051c233fd72033f0c3b5a8c1965260e7e19f)
- support for additional languages: [pt-br (Portuguese (Brasil)), fa (Persian (Farsi))](131504e7eed8b3400c457fbe49beea3b115bc916)
- support for [three (two optional) subtitle languages](e543c927cf49c264eaece36640c99d67a99c7da2)
- optionally use [random user agent for addic7ed provider](83ace14faf75fbd75313f0ceda9b78161895fbcf) (should not be needed)
