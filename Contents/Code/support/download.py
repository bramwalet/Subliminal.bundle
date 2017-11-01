# coding=utf-8

import subliminal_patch as subliminal

from support.config import config
from support.helpers import cast_bool
from subtitlehelpers import get_subtitles_from_metadata
from subliminal_patch import compute_score


def download_best_subtitles(video_part_map, min_score=0):
    hearing_impaired = Prefs['subtitles.search.hearingImpaired']
    ietf_as_alpha3 = cast_bool(Prefs["subtitles.language.ietf_normalize"])
    languages = config.lang_list.copy()
    if not languages:
        return

    # should we treat IETF as alpha3? (ditch the country part)
    if ietf_as_alpha3:
        languages = list(languages)
        for language in languages:
            language.country_orig = language.country
            language.country = None

        languages = set(languages)

    missing_languages = False
    for video, part in video_part_map.iteritems():
        if not Prefs['subtitles.save.filesystem']:
            # scan for existing metadata subtitles
            meta_subs = get_subtitles_from_metadata(part)
            for language, subList in meta_subs.iteritems():
                if subList:
                    video.subtitle_languages.add(language)
                    Log.Debug("Found metadata subtitle %s for %s", language, video)

        have_languages = video.subtitle_languages.copy()
        if ietf_as_alpha3:
            have_languages = list(have_languages)
            for language in have_languages:
                language.country_orig = language.country
                language.country = None
            have_languages = set(have_languages)

        missing_subs = (languages - have_languages)

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
        # re-add country codes to the missing languages, in case we've removed them above
        if ietf_as_alpha3:
            for language in languages:
                if language.country_orig:
                    language.country = language.country_orig

        Log.Debug("Download best subtitles using settings: min_score: %s, hearing_impaired: %s, languages: %s" %
                  (min_score, hearing_impaired, languages))

        return subliminal.download_best_subtitles(video_part_map.keys(), languages, min_score, hearing_impaired, providers=config.providers,
                                                  provider_configs=config.provider_settings, pool_class=config.provider_pool,
                                                  compute_score=compute_score)
    Log.Debug("All languages for all requested videos exist. Doing nothing.")