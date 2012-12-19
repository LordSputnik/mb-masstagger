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

import json
import time

from collections import deque

import mutagen.oggvorbis
import mutagen.flac

import musicbrainzngs as ws

import Warp.compatid3
import Warp.track
import Warp.release


from Warp.utils import *

num_total_songs = 0

albums_fetch_queue = deque()
albums = {}
options = {}
skipped_files = list()
num_passes = 0

num_completed_releases = 0
last_num_completed_releases = None
no_new_albums = False

ValidFileTypes = [
    "flac",
    "ogg",
    "mp3",
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
    global last_fetch_time
    if (time.time() - last_fetch_time) < 1:
        return None

    last_fetch_time = time.time()

    if len(albums_fetch_queue) > 0:
        release_id = albums_fetch_queue.popleft()
        result = albums[release_id]

        if not result.valid:
            return None

        result.Fetch()

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
            albums[release_id] = Warp.release.Release(release_id)

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

def SyncMetadata(release):
    global num_processed_songs

    if not release.valid:
        return

    release.Sync(options)

    return

###############################################
### Main Script Loop ##########################
###############################################

PrintHeader()

ws.set_rate_limit() #Disable the default rate limiting, as I do my own, and don't know whether this is blocking/non-blocking.
ws.set_useragent("mb-masstagger-py","0.1","ben.sput@gmail.com")

if os.path.exists("./options"):
    ReadOptions("./options")
elif os.path.exists("./options.default"):
    ReadOptions("./options.default")

#result = ws.get_release_by_id("6ad1068f-2f51-4079-9b44-25e0734f97ff",["artist-credits","recordings","labels","release-groups","media"])["release"]
#print json.dumps(result, sort_keys=True, indent=4)
last_fetch_time = 0

if os.path.isdir(options["library_folder"]):
    options["library_folder"] = os.path.realpath(options["library_folder"])
else:
    options["library_folder"] = os.path.realpath("./")

ignores = list()
for dirname, dirnames, filenames in os.walk(options["library_folder"]):
    if "warp-ignore" in filenames:
        del filenames[:]
        del dirnames[:]
    for filename in filenames:
        if os.path.splitext(filename)[1][1:] in ValidFileTypes: # Compares extension to valid extensions.
            num_total_songs += 1

print ("Found {} songs to update.".format(num_total_songs))
print ("Updating...\n")

while num_completed_releases != last_num_completed_releases:

    last_num_completed_releases = len(albums)
    num_passes += 1

    for dirname, dirnames, filenames in os.walk(options["library_folder"]):
        if "warp-ignore" in filenames:
            del filenames[:]
            del dirnames[:]
        for filename in filenames:

            if (Warp.track.Track.num_loaded > 1000) or (len(albums) > 100):
                no_new_albums = True

            release_id = None
            audio = None
            track = None
            file_ext = os.path.splitext(filename)[1][1:]
            is_audio_file = False

            abs_file_path = unicode(os.path.realpath(os.path.join(dirname,filename)),encoding="utf-8")
            if file_ext == "mp3":
                try:
                    audio = Warp.compatid3.CompatID3(abs_file_path)
                except mutagen.id3.ID3NoHeaderError:
                    print ("Invalid MP3 File: " + abs_file_path)
                else:
                    is_audio_file = True
                    if audio.has_key("TXXX:MusicBrainz Album Id"):
                        release_id = str(audio["TXXX:MusicBrainz Album Id"])
                        track = Warp.track.MP3Track(audio,file_ext,options)
                    else:
                        print "Song: " + audio.filename + " doesn't have tag:"
                        for key,value in audio.items():
                            if str(key)[0:4] != "APIC":
                                print "K: " + str(key) + " V: " + str(value)


            elif file_ext == "flac":
                try:
                    audio = mutagen.flac.FLAC(abs_file_path)
                except mutagen.flac.FLACNoHeaderError:
                    print ("Invalid FLAC File: " + abs_file_path)
                else:
                    is_audio_file = True
                    if audio.has_key("musicbrainz_albumid"):
                        release_id = str(audio["musicbrainz_albumid"][0])
                        track = Warp.track.FLACTrack(audio,file_ext,options)

            elif file_ext == "ogg":
                try:
                    audio = mutagen.oggvorbis.OggVorbis(abs_file_path)
                except mutagen.oggvorbis.OggVorbisHeaderError:
                    print ("Invalid Ogg File: " + abs_file_path)
                else:
                    is_audio_file = True
                    if audio.has_key("musicbrainz_albumid"):
                        is_audio_file = True
                        release_id = str(audio["musicbrainz_albumid"][0])
                        track = Warp.track.OggTrack(audio,file_ext,options)

            if release_id != None:

                if (no_new_albums == False) or ((no_new_albums == True) and (release_id in albums.keys())):
                    release = RequestRelease(release_id)

                    if release is not None:
                        track.release = release
                        release.AddSong(track)

            elif is_audio_file:
                if str(dirname+"/"+filename) not in skipped_files:
                    skipped_files.append(str(dirname+"/"+filename))


    while len(albums_fetch_queue) > 0:
        fetched_release = FetchNextRelease()
        if fetched_release != None:
            print "\nID: " + fetched_release.id + " with " + str(len(fetched_release.songs)) + " songs."
            SyncMetadata(fetched_release)
            fetched_release.Close()
            print ("Pass {}: {} songs remaining to process and {}/{} processed.\n".format(num_passes, Warp.track.Track.num_loaded, Warp.track.Track.num_processed, num_total_songs))


    num_completed_releases = len(albums)
    no_new_albums = False
    #print ("Albums processed: " + str(num_completed_releases) + " Last Album Total: " + str(last_num_completed_releases))

print ("\n-------------------------------------------------")
print ("Checked {} MP3s, {} OGGs and {} FLACs.".format(Warp.track.MP3Track.count, Warp.track.OggTrack.count, Warp.track.FLACTrack.count))
if len(skipped_files) > 0:
    print ("Skipped {} files with no MB Release ID:".format(len(skipped_files)))
    for s in skipped_files:
        print " " + s
