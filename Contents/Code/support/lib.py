# coding=utf-8

from plex import Plex
from auth import refresh_plex_token


def configure_plex():
    # this may be the only viable usage of global :O (correct me if i'm wrong)
    global Plex
    if not "token" in Dict or not (Prefs["plex_username"] and Prefs["plex_password"]):
        refresh_plex_token()

    # initialize Plex api
    Plex.configuration.defaults.authentication(Dict["token"] if "token" in Dict else None)


lib_unaccessible_error = "\n\n\n!!!!!!!!!!!!!! ATTENTION !!!!!!!!!!!!! \nCan't access your Plex Media Servers' API.\nAre you using Plex Home?"" \
""Please configure your Plex.tv credentials! Advanced features disabled!\n\n\n"
