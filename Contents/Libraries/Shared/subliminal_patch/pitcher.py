# coding=utf-8

import time
import logging
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask, NoCaptchaTask, AnticaptchaException


logger = logging.getLogger(__name__)


class PitcherRegistry(object):
    pitchers = {}

    def register(self, cls):
        self.pitchers[cls.name] = cls
        return cls

    def get_pitcher(self, name):
        return self.pitchers[name]


registry = pitchers = PitcherRegistry()


class Pitcher(object):
    name = None
    tries = 3
    client_key = None
    job = None
    client = None

    def __init__(self, client_key, tries=3):
        self.client_key = client_key
        self.tries = tries

    def get_client(self):
        raise NotImplementedError

    def get_job(self):
        raise NotImplementedError

    def throw(self):
        self.client = self.get_client()
        self.job = self.get_job()


@registry.register
class AntiCaptchaProxyLessPitcher(Pitcher):
    name = "AntiCaptchaProxyLess"
    host = "api.anti-captcha.com"
    language_pool = "en"
    use_ssl = True
    website_url = None
    website_key = None
    website_name = None

    def __init__(self, website_name, client_key, website_url, website_key, tries=3, host=None, language_pool=None,
                 use_ssl=True):
        super(AntiCaptchaProxyLessPitcher, self).__init__(client_key, tries=tries)
        self.host = host or self.host
        self.language_pool = language_pool or self.language_pool
        self.use_ssl = use_ssl
        self.website_name = website_name
        self.website_key = website_key
        self.website_url = website_url

    def get_client(self):
        return AnticaptchaClient(self.client_key, self.language_pool, self.host, self.use_ssl)

    def get_job(self):
        task = NoCaptchaTaskProxylessTask(website_url=self.website_url, website_key=self.website_key)
        return self.client.createTask(task)

    def throw(self):
        for i in range(self.tries):
            super(AntiCaptchaProxyLessPitcher, self).throw()
            try:
                self.job.join()
                return self.job.get_solution_response()
            except AnticaptchaException as e:
                if i >= self.tries - 1:
                    logger.error("%s: Captcha solving finally failed. Exiting", self.website_name)
                    return

                if e.error_code == 'ERROR_ZERO_BALANCE':
                    logger.error("%s: No balance left on captcha solving service. Exiting", self.website_name)
                    return

                elif e.error_code == 'ERROR_NO_SLOT_AVAILABLE':
                    logger.info("%s: No captcha solving slot available, retrying", self.website_name)
                    time.sleep(5.0)
                    continue

                elif e.error_code == 'ERROR_KEY_DOES_NOT_EXIST':
                    logger.error("%s: Bad AntiCaptcha API key", self.website_name)
                    return

                elif e.error_id is None and e.error_code == 250:
                    # timeout
                    if i < self.tries:
                        logger.info("%s: Captcha solving timed out, retrying", self.website_name)
                        time.sleep(1.0)
                        continue
                    else:
                        logger.error("%s: Captcha solving timed out three times; bailing out", self.website_name)
                        return
                raise

