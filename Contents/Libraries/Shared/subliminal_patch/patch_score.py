# coding=utf-8

import logging

from subliminal.video import Episode, Movie
from subliminal.score import get_scores

logger = logging.getLogger(__name__)


def compute_score(matches, subtitle, video, hearing_impaired=None):
    """Compute the score of the `subtitle` against the `video` with `hearing_impaired` preference.
    
    patch: 
        - remove upper bounds of score
        - re-add matches argument and remove get_matches from here

    :func:`compute_score` uses the :meth:`Subtitle.get_matches <subliminal.subtitle.Subtitle.get_matches>` method and
    applies the scores (either from :data:`episode_scores` or :data:`movie_scores`) after some processing.

    :param subtitle: the subtitle to compute the score of.
    :type subtitle: :class:`~subliminal.subtitle.Subtitle`
    :param video: the video to compute the score against.
    :type video: :class:`~subliminal.video.Video`
    :param bool hearing_impaired: hearing impaired preference.
    :return: score of the subtitle.
    :rtype: int

    """
    logger.info('Computing score of %r for video %r with %r', subtitle, video, dict(hearing_impaired=hearing_impaired))

    # get the scores dict
    scores = get_scores(video)
    logger.debug('Using scores %r', scores)

    # on hash match, discard everything else
    if 'hash' in matches:
        logger.debug('Keeping only hash match')
        matches &= {'hash'}

    # handle equivalent matches
    if isinstance(video, Episode):
        if 'title' in matches:
            logger.debug('Adding title match equivalent')
            matches.add('episode')
        if 'series_imdb_id' in matches:
            logger.debug('Adding series_imdb_id match equivalent')
            matches |= {'series', 'year'}
        if 'imdb_id' in matches:
            logger.debug('Adding imdb_id match equivalents')
            matches |= {'series', 'year', 'season', 'episode'}
        if 'tvdb_id' in matches:
            logger.debug('Adding tvdb_id match equivalents')
            matches |= {'series', 'year', 'season', 'episode'}
        if 'series_tvdb_id' in matches:
            logger.debug('Adding series_tvdb_id match equivalents')
            matches |= {'series', 'year'}
    elif isinstance(video, Movie):
        if 'imdb_id' in matches:
            logger.debug('Adding imdb_id match equivalents')
            matches |= {'title', 'year'}

    # handle hearing impaired
    if hearing_impaired is not None and subtitle.hearing_impaired == hearing_impaired:
        logger.debug('Matched hearing_impaired')
        matches.add('hearing_impaired')

    # compute the score
    score = sum((scores.get(match, 0) for match in matches))
    logger.info('Computed score %r with final matches %r', score, matches)

    # ensure score is within valid bounds
    assert 0 <= score

    return score