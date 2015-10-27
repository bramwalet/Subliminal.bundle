# coding=utf-8


# thanks, https://github.com/drzoidberg33/plexpy/blob/master/plexpy/plextv.py

class PlexTV(object):
    """
    Plex.tv authentication
    """

    def __init__(self, username=None, password=None):
        self.protocol = 'HTTPS'
        self.username = username
        self.password = password
        self.ssl_verify = plexpy.CONFIG.VERIFY_SSL_CERT

        self.request_handler = http_handler.HTTPHandler(host='plex.tv',
                                                        port=443,
                                                        token=plexpy.CONFIG.PMS_TOKEN,
                                                        ssl_verify=self.ssl_verify)

    def get_plex_auth(self, output_format='raw'):
        uri = '/users/sign_in.xml'
        base64string = base64.encodestring('%s:%s' % (self.username, self.password)).replace('\n', '')
        headers = {'Content-Type': 'application/xml; charset=utf-8',
                   'Content-Length': '0',
                   'X-Plex-Device-Name': 'PlexPy',
                   'X-Plex-Product': 'PlexPy',
                   'X-Plex-Version': 'v0.1 dev',
                   'X-Plex-Client-Identifier': plexpy.CONFIG.PMS_UUID,
                   'Authorization': 'Basic %s' % base64string + ":"
                   }

        request = self.request_handler.make_request(uri=uri,
                                                    proto=self.protocol,
                                                    request_type='POST',
                                                    headers=headers,
                                                    output_format=output_format)

        return request

    def get_token(self):
        plextv_response = self.get_plex_auth(output_format='xml')

        if plextv_response:
            xml_head = plextv_response.getElementsByTagName('user')
            if not xml_head:
                logger.warn("Error parsing XML for Plex.tv token")
                return []

            auth_token = xml_head[0].getAttribute('authenticationToken')

            return auth_token
        else:
            return []