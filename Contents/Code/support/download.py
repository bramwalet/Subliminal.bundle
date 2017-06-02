# coding=utf-8

import subliminal_patch as subliminal

from support.config import config
from subtitlehelpers import get_subtitles_from_metadata
from subliminal_patch import compute_score


def download_best_subtitles(video_part_map, min_score=0):
    hearing_impaired = Prefs['subtitles.search.hearingImpaired']
    languages = config.lang_list
    if not languages:
        return

    missing_languages = False
    for video, part in video_part_map.iteritems():
        if not Prefs['subtitles.save.filesystem']:
            # scan for existing metadata subtitles
            meta_subs = get_subtitles_from_metadata(part)
            for language, subList in meta_subs.iteritems():
                if subList:
                    video.subtitle_languages.add(language)
                    Log.Debug("Found metadata subtitle %s for %s", language, video)

        missing_subs = (languages - video.subtitle_languages)

        # all languages are found if we either really have subs for all languages or we only want to have exactly one language
        # and we've only found one (the case for a selected language, Prefs['subtitles.only_one'] (one found sub matches any language))
        found_one_which_is_enough = len(video.subtitle_languages) >= 1 and Prefs['subtitles.only_one']
        if not missing_subs or found_one_which_is_enough:
            if found_one_which_is_enough:
                Log.Debug('Only one language was requested, and we\'ve got a subtitle for %s', video)
            else:
                Log.Debug('All languages %r exist for %s', languages, video)
            continue
        missing_languages = True
        break

    if missing_languages:
        Log.Debug("Download best subtitles using settings: min_score: %s, hearing_impaired: %s" % (min_score, hearing_impaired))

        return subliminal.download_best_subtitles(video_part_map.keys(), languages, min_score, hearing_impaired, providers=config.providers,
                                                  provider_configs=config.provider_settings, pool_class=config.provider_pool,
                                                  compute_score=compute_score)
    Log.Debug("All languages for all requested videos exist. Doing nothing.")