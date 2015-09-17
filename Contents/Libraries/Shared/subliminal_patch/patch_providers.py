# coding=utf-8

from random import randint
from subliminal.providers.addic7ed import Addic7edProvider
from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST

class PatchedAddic7edProvider(Addic7edProvider):
    def initialize(self):
	super(PatchedAddic7edProvider, self).initialize()
	self.session.headers = {
            'User-Agent': AGENT_LIST[randint(0, len(AGENT_LIST)-1)],
            'Referer': self.server_url,
        }