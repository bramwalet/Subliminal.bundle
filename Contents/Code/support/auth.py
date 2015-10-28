# coding=utf-8

import sys
import uuid

def refresh_plex_token():
    username = Prefs["plex_username"]
    password = Prefs["plex_password"]

    if not username or not password:
	if "token" in Dict:
	    del Dict["token"]
	    Dict.Save()
	return

    if not "uuid" in Dict:
	Dict["uuid"] = uuid.uuid1()
	Dict.Save()

    current_uuid = Dict["uuid"]

    headers = {
               'X-Plex-Device-Name': 'Sub-Zero',
               'X-Plex-Product': 'Sub-Zero',
               'X-Plex-Version': '1.3.0',
               'X-Plex-Client-Identifier': "%s" % current_uuid,
               }

    request = HTTP.Request("https://plex.tv/users/sign_in.json", headers=headers, values={'user[login]': Prefs["plex_username"], 'user[password]': Prefs["plex_password"]}, immediate=True)
    token = None
    if request:
	try:
    	    data = JSON.ObjectFromString(request.content)
	    token = data["user"]["authentication_token"]
	    Log.Debug("Data returned from plex.tv: %s", data)
	except:
	    pass
	if token:
	    Dict["token"] = token
	    Dict.Save()
	    return True

