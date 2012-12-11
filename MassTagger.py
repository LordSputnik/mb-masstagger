# Copyright (C) 2012 Ben Ockmore

# This file is part of MusicBrainz MassTagger.

# MusicBrainz MassTagger is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# MusicBrainz MassTagger is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with MusicBrainz MassTagger. If not, see <http://www.gnu.org/licenses/>.

import os
import urllib2
import time
import mutagen.oggvorbis
import mutagen.flac
import base64
from collections import defaultdict
from collections import deque
import musicbrainzngs as ws
import json
import compatid3
import entities

from utils import *

num_current_songs = num_processed_songs = num_total_songs = 0

albums_fetch_queue = deque()
albums = {}
options = {}
songs = defaultdict(list)
skipped_files = list()
num_passes = 0

num_albums = 0
last_num_albums = None
no_new_albums = False

song_ids = list()

ValidFileTypes = [
    ".flac",
    ".ogg",
    ".mp3",
]

def PrintHeader():
    print (
"\
----------------------------------------------------\n\
| MusicBrainz Warp - 0.1                           |\n\
| Created by Ben Ockmore AKA LordSputnik, (C) 2012 |\n\
----------------------------------------------------\n\n\
Starting..."
)
    return

def FetchNextRelease():
    global last_time
    if (time.time() - last_time) < 1:
        return None

    last_time = time.time()

    if len(albums_fetch_queue) > 0:
        release_id = albums_fetch_queue.popleft()
        result = albums[release_id]

        if not result.valid:
            return None

        result.fetch()

        if result.fetched:
            return result

        else:
            return None
    else:
        return None

def RequestRelease(release_id):
    global albums

    if release_id not in albums:

        if release_id not in albums_fetch_queue:
            albums_fetch_queue.append(release_id)
            albums[release_id] = entities.Release(release_id)

    return albums[release_id]

def InterpretOptionValue(value):

    if value.startswith("y") or value == "1":
        return True

    elif value.startswith("n") or value == "0":
        return False

    else:
        return value.replace("\"","").replace("\n","")

def ReadOptions(file_name):
    f = open(file_name,"r")

    print "\nReading Options..."
    for line in f:
        words = line.split("=")

        if len(words) > 1:
            options[words[0]] = InterpretOptionValue(words[1])
            print "{} = {}".format(words[0], options[words[0]])

    print "\n"

###############################################
### Metadata Syncing Functions ################
###############################################

def SyncMP3MetaData(song,release):
    return

def SyncFLACMetaData(song,release):
    entities.FLACTrack.count += 1
    song.Sync(options)
    song.Save(options)

    print "Updating \"" + song.file[u"title"][0] + "\" by " + song.file["artist"][0]

    return

def SyncVorbisMetaData(song,release):
    entities.OggTrack.count += 1
    song.Sync(options)
    song.Save(options)

    print "Updating \"" + song.file[u"title"][0] + "\" by " + song.file["artist"][0]

    return

def SyncMetadata(song, release):
    global num_processed_songs

    if not release.valid:
        return

    num_processed_songs += 1

    if song.ext == "mp3":
        SyncMP3MetaData(song,release)

    elif song.ext == "flac":
        SyncFLACMetaData(song,release)

    elif song.ext == "ogg":
        SyncVorbisMetaData(song,release)

    else:
        num_processed_songs -= 1

    return

###############################################
### Main Script Loop ##########################
###############################################

PrintHeader()

ws.set_rate_limit() #Disable the default rate limiting, as I do my own, and don't know whether this is blocking/non-blocking.
ws.set_useragent("mb-masstagger-py","0.1","ben.sput@gmail.com")

if os.path.exists("./options"):
    ReadOptions("./options")

#result = ws.get_release_by_id("75b34c4a-1e15-3bf5-a734-abfafa94c731",["artist-credits","recordings","labels","isrcs","release-groups"])["release"]
#print json.dumps(result, sort_keys=True, indent=4)
last_time = 0

for dirname, dirnames, filenames in os.walk('.'):
    for filename in filenames:
        if os.path.splitext(filename)[1] in ValidFileTypes: # Compares extension to valid extensions.
            num_total_songs += 1

print ("Found {} songs to update.".format(num_total_songs))
print ("Updating...\n")

while num_albums != last_num_albums:

    last_num_albums = len(albums)
    num_passes += 1

    for dirname, dirnames, filenames in os.walk('.'):

        for filename in filenames:

            if (num_current_songs > 1000) or (len(albums) > 100):
                no_new_albums = True

            release_id = None
            audio = None
            track = None
            file_ext = os.path.splitext(filename)[1][1:]
            is_audio_file = False

            if file_ext == "mp3":
                try:
                    audio = compatid3.CompatID3(dirname+"/"+filename)
                except mutagen.id3.ID3NoHeaderError:
                    print ("Invalid MP3 File")
                else:
                    is_audio_file = True
                    if audio.has_key("TXXX:musicbrainz_albumid"):
                        release_id = str(audio["TXXX:musicbrainz_albumid"])
                        track = entities.MP3Track(audio,file_ext)

            elif file_ext == "flac":
                try:
                    audio = mutagen.flac.FLAC(dirname+"/"+filename)
                except mutagen.flac.FLACNoHeaderError:
                    print ("Invalid FLAC File")
                else:
                    is_audio_file = True
                    if audio.has_key("musicbrainz_albumid"):
                        release_id = str(audio["musicbrainz_albumid"][0])
                        track = entities.FLACTrack(audio,file_ext)

            elif file_ext == "ogg":
                audio = mutagen.oggvorbis.OggVorbis(dirname+"/"+filename)
                if audio.has_key("musicbrainz_albumid"):
                    is_audio_file = True
                    release_id = str(audio["musicbrainz_albumid"][0])
                    track = entities.OggTrack(audio,file_ext)

            if release_id != None:

                if (no_new_albums == False) or ((no_new_albums == True) and (release_id in albums.keys())):
                    release = RequestRelease(release_id)

                    if release is not None:
                        track.release = release
                        release.add_song(track)
                        num_current_songs += 1

            elif is_audio_file:
                if str(dirname+"/"+filename) not in skipped_files:
                    skipped_files.append(str(dirname+"/"+filename))


    while len(albums_fetch_queue) > 0:
        fetched_release = FetchNextRelease()
        if fetched_release != None:
            print "\nID: " + fetched_release.id + " with " + str(len(fetched_release.songs)) + " songs."
            for s in fetched_release.songs:
                SyncMetadata(s,fetched_release)
            num_current_songs -= len(fetched_release.songs)
            print ("Pass {}: {} songs remaining to process and {}/{} processed.\n".format(num_passes, num_current_songs, num_processed_songs, num_total_songs))

    for album in albums.values():
        album.close()

    num_albums = len(albums)
    no_new_albums = False
    #print ("Albums processed: " + str(num_albums) + " Last Album Total: " + str(last_num_albums))

print ("\n-------------------------------------------------")
print ("Checked {} MP3s, {} OGGs and {} FLACs.".format(entities.MP3Track.count, entities.OggTrack.count, entities.FLACTrack.count))
if len(skipped_files) > 0:
    print ("Skipped {} files with no MB Release ID:".format(len(skipped_files)))
    for s in skipped_files:
        print " " + s
