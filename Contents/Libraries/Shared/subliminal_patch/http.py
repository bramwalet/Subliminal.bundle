# coding=utf-8

import certifi

import os
from requests import Session
from retry.api import retry_call


class RetryingSession(Session):
    proxied_functions = ("get", "post")

    def __init__(self):
        super(RetryingSession, self).__init__()
        self.verify = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", certifi.where()))

    def retry_method(self, method, *args, **kwargs):
        return retry_call(getattr(super(RetryingSession, self), method), fargs=args, fkwargs=kwargs, tries=3, delay=1)

    def get(self, *args, **kwargs):
        return self.retry_method("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.retry_method("post", *args, **kwargs)
