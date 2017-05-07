# coding=utf-8

from subliminal.providers import Provider as _Provider


class Provider(_Provider):
    hash_verifiable = False
    skip_wrong_fps = True

