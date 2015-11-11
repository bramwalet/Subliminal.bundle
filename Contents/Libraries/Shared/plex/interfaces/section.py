from plex.core.idict import idict
from plex.interfaces.core.base import Interface


class SectionInterface(Interface):
    path = 'library/sections'

    def all(self, key):
        response = self.http.get(key, 'all')

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Directory': {
                    'artist':   'Artist',
                    'show':     'Show'
                },
                'Video': {
                    'movie':    'Movie'
                }
            }))
        }))

    def first_character(self, key, character=None):
        if character:
            response = self.http.get(key, ['firstCharacter', character])
            return self.parse(response, idict({
                'MediaContainer': ('MediaContainer', idict({
                    'Directory': {
                        'artist': 'Artist',
                        'show': 'Show'
                    },
                    'Video': {
                        'movie': 'Movie'
                    }
                }))
            }))

        response = self.http.get(key, 'firstCharacter')

        return self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Directory': 'Directory'
            }))
        }))
