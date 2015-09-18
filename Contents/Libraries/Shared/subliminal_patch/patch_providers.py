# coding=utf-8

import logging
from random import randint
from subliminal.providers.addic7ed import Addic7edProvider

logger = logging.getLogger(__name__)

class PatchedAddic7edProvider(Addic7edProvider):
    USE_ADDICTED_RANDOM_AGENTS = False

    def __init__(self, username=None, password=None, use_random_agents=False):
	super(PatchedAddic7edProvider, self).__init__(username=username, password=password)
	self.USE_ADDICTED_RANDOM_AGENTS = use_random_agents

    def initialize(self):
	super(PatchedAddic7edProvider, self).initialize()
	if self.USE_ADDICTED_RANDOM_AGENTS:
	    from .utils import FIRST_THOUSAND_OR_SO_USER_AGENTS as AGENT_LIST
	    logger.debug("addic7ed: using random user agents")
	    self.session.headers = {
        	'User-Agent': AGENT_LIST[randint(0, len(AGENT_LIST)-1)],
        	'Referer': self.server_url,
    	    }
