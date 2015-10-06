Enzyme
======

Enzyme is a Python module to parse video metadata.

.. image:: https://travis-ci.org/Diaoul/enzyme.png?branch=master
    :target: https://travis-ci.org/Diaoul/enzyme


Usage
-----

Parse a MKV file metadata:

    >>> import enzyme
    >>> with open('example.mkv', 'rb') as f:
    ...     mkv = enzyme.MKV(f)
    ... 
    >>> mkv.info
    <Info [title=None, duration=0:00:01.440000, date=2015-03-14 08:40:16]>
    >>> mkv.video_tracks
    [<VideoTrack [2, 720x576, V_DIRAC, name=u'Video\x00', language=None]>]
    >>> mkv.audio_tracks
    [<AudioTrack [1, 2 channel(s), 44100Hz, A_MS/ACM, name=u'Audio\x00', language=None]>]

License
-------

Copyright 2013-2015 Antoine Bertin

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
