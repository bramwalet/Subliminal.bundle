# coding=utf-8


def refresh_plex_token():
    username = Prefs["plex_username"]
    password = Prefs["plex_password"]

    if not username or not password:
        if "token" in Dict:
            del Dict["token"]
            Dict.Save()
        return

    if "uuid" not in Dict:
        Dict["uuid"] = String.UUID()
        Dict.Save()

    current_uuid = Dict["uuid"]

    headers = {
        'X-Plex-Device-Name': 'Sub-Zero',
        'X-Plex-Product': 'Sub-Zero',
        'X-Plex-Version': '1.3.0',
        'X-Plex-Client-Identifier': "%s" % current_uuid,
    }

    request = HTTP.Request("https://plex.tv/users/sign_in.json", headers=headers,
                           values={'user[login]': Prefs["plex_username"], 'user[password]': Prefs["plex_password"]}, immediate=True)
    token = None
    if request:
        try:
            data = JSON.ObjectFromString(request.content)
            token = data["user"]["authentication_token"]
            log_data = data.copy()
            log_data["user"]["authentication_token"] = "xxxxxxxxxxxxxxxxxx"
            Log.Debug("Data returned from plex.tv: %s", log_data)
        except:
            pass
        if token:
            Dict["token"] = token
            Dict.Save()
            return True
