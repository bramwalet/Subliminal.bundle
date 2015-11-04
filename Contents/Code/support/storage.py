# coding=utf-8

import datetime

def storeSubtitleInfo(videos, subtitles, storage_type):
    """
    stores information about downloaded subtitles in plex's Dict()
    """
    if not "subs" in Dict:
	Dict["subs"] = {}

    storage = Dict["subs"]

    for video, video_subtitles in subtitles.items():
	part = videos[video]

	if not video.id in storage:
	    storage[video.id] = {}

	video_dict = storage[video.id]
	if not part.id in video_dict:
	    video_dict[part.id] = {}

	part_dict = video_dict[part.id]
	for subtitle in video_subtitles:
	    lang = Locale.Language.Match(subtitle.language.alpha2)
	    if not lang in part_dict:
		part_dict[lang] = {}
	    lang_dict = part_dict[lang]
	    sub_key = (subtitle.provider_name, subtitle.id)
	    lang_dict[sub_key] = dict(score=subtitle.score, link=subtitle.page_link, storage=storage_type, hash=Hash.MD5(subtitle.content), date_added=datetime.datetime.now())

    Dict.Save()

def resetStorage(key):
    """
    resets the Dict[key] storage, thanks to https://docs.google.com/document/d/1hhLjV1pI-TA5y91TiJq64BdgKwdLnFt4hWgeOqpz1NA/edit#
    We can't use the nice Plex interface for this, as it calls get multiple times before set
	#Plex[":/plugins/*/prefs"].set("com.plexapp.agents.subzero", "reset_storage", False)
    """

    Log.Debug("resetting storage")
    Dict[key] = {}
    Dict.Save()


def logStorage(key):
    if key in Dict:
	Log.Debug(Dict[key])