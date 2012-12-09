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

num_flacs = num_mp3s = num_oggs = num_current_songs = num_processed_songs = num_total_songs = 0

library_folder = ""

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

VorbisRecordingTags = {
    "artist-credit-phrase":"artist",
    "title":"title",
    "id":"musicbrainz_trackid"
}

def DetectLibraryFolder(filenames):
    global library_folder

    for file in filenames:
        print file

    possible_library_folder = os.path.commonprefix(filenames)
    if os.path.isdir(possible_library_folder):
        library_folder = possible_library_folder

    print library_folder

def PrintHeader():
    print ("\
----------------------------------------------------\n\
| MusicBrainz Warp - 0.1                           |\n\
| Created by Ben Ockmore AKA LordSputnik, (C) 2012 |\n\
----------------------------------------------------\n\n\
Starting...")
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

def RequestNextRelease(release_id):
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
        return value.replace("\"","")

def ReadOptions(file_name):
    f = open(file_name,"r")
    for line in f:
        words = line.split("=")
        if len(words) > 1:
            options[words[0]] = InterpretOptionValue(words[1])
            print "{} = {}".format(words[0], options[words[0]])

###############################################
### Metadata Syncing Functions ################
###############################################

def SaveFile(audio_file, metadata, track_num, disc_num):
    audio_file[0].save()

    dest_name = ""
    disc_string = "{"+":0>{}".format(len(metadata["totaldiscs"][0])) + "}"
    track_string = "{"+":0>{}".format(len(metadata["totaltracks"][0])) + "}"
    if options["rename-files"]:
        if int(metadata["totaldiscs"][0]) == 1:
            dest_name = options["rename-format"]
            dest_name = dest_name.replace("#",track_string.format(track_num)).replace("T","{}.{}".format(metadata["title"][0],audio_file[1]))
        else:
            dest_name = options["multi-disc-rename-format"]
            dest_name = dest_name.replace("D",disc_string.format(disc_num)).replace("#",track_string.format(track_num)).replace("T","{}.{}".format(metadata["title"][0],audio_file[1]))

        print dest_name

        
        os.rename(audio_file[0].filename,os.path.join(library_folder,"{:0>2}. {}.{}".format(track_num,metadata["title"][0],audio_file[1])))

def GetVorbisCommentMetadata(song, release):
    release_data = release.data
    recording = None
    metadata = {}

    #Get the recording info for the song.
    total_discs = len(release_data["medium-list"])

    #TODO - Move this out of the function so that we can specialize to the correct tag for each file format. Perhaps put in Song class.
    if song.has_key("discnumber"):
        discnumber = song["discnumber"][0]
    elif total_discs == 1:
        discnumber = "1"
    else:
        print "Error, no disc number for multi-disc release!"
        return None
        
    metadata.setdefault("totaldiscs", []).append(str(len(release_data["medium-list"])))
    for medium in release_data["medium-list"]:
        if medium["position"] == discnumber:
            metadata.setdefault("discnumber", []).append(medium["position"])
            metadata.setdefault("totaltracks", []).append(str(len(medium["track-list"])))
            for t in medium["track-list"]:
                if t["position"] == song["tracknumber"][0]:
                    metadata.setdefault("tracknumber", []).append(t["position"])
                    recording = t["recording"]

    if recording is None: #Couldn't find the recording - we can't do anything (except maybe look for recording id).
        return None

    for key,value in recording.items():
        if VorbisRecordingTags.has_key(key):
            metadata.setdefault(VorbisRecordingTags[key], []).append(value)
        elif key == "artist-credit":
            i = 0
            artist_sort_name = ""
            for c in value:
                if i == 0: #artist
                    artist_sort_name += c["artist"]["sort-name"]
                    metadata.setdefault("musicbrainz_artistid", []).append(c["artist"]["id"])
                else: #join phrase
                    artist_sort_name += c
                i ^= 1
            metadata.setdefault("artistsort", []).append(artist_sort_name)

    return metadata

def SyncMP3MetaData(song,release):
    return

def SyncFLACMetaData(song,release):
    metadata = GetVorbisCommentMetadata(song[0],release)
    if metadata == None:
        return

    tags = {}

    if options["clear-tags"]:
        song[0].delete()

    for key,value in release.processed_data.items():
        tags[key.upper().encode("utf-8")] = value

    for key,value in metadata.items():
        tags[key.upper().encode("utf-8")] = value

    cover_art = release.art
    if cover_art != None:
        song[0].clear_pictures();
        picture = mutagen.flac.Picture()
        picture.data = cover_art[4]
        picture.mime = "image/jpeg"
        picture.desc = ""
        picture.type = 3
        song[0].add_picture(picture)

    song[0].update(tags)
    
    SaveFile(song,metadata,song[0][u"tracknumber"][0],"1")
    print "Updating \"" + song[0][u"title"][0] + "\" by " + song[0]["artist"][0]

    return

def SyncVorbisMetaData(song,release):
    metadata = GetVorbisCommentMetadata(song[0],release)
    if metadata == None:
        return
        
    tags = {}

    if options["clear-tags"]:
        song[0].delete()

    for key,value in metadata.items():
        tags[key.upper().encode("utf-8")] = value

    cover_art = release.art
    if cover_art != None:
        if song[0].has_key(u"METADATA_BLOCK_PICTURE"):
            song[0][u"METADATA_BLOCK_PICTURE"] = []
        picture = mutagen.flac.Picture()
        picture.data = cover_art[4]
        picture.mime = "image/jpeg"
        picture.desc = ""
        picture.type = 3
        tags.setdefault(u"METADATA_BLOCK_PICTURE", []).append(base64.standard_b64encode(picture.write()))

    song[0].update(tags)
    SaveFile(song,metadata,song[0][u"tracknumber"][0],"1")

    print "Updating \"" + song[0][u"title"][0] + "\" by " + song[0]["artist"][0]


    return

def SyncMetadata(song, release):
    global num_flacs, num_mp3s, num_oggs, num_processed_songs

    if not release.valid:
        return

    num_processed_songs += 1

    if song[1] == "mp3":
        num_mp3s += 1
        SyncMP3MetaData(song,release)
    elif song[1] == "flac":
        num_flacs += 1
        SyncFLACMetaData(song,release)
    elif song[1] == "ogg":
        num_oggs += 1
        SyncVorbisMetaData(song,release)
    else:
        num_processed_songs -= 1

    return

###############################################
### Main Script Loop ##########################
###############################################

ws.set_rate_limit() #Disable the default rate limiting, as I do my own, and don't know whether this is blocking/non-blocking.
ws.set_useragent("mb-masstagger-py","0.1","ben.sput@gmail.com")

if os.path.exists("./options"):
    ReadOptions("./options")

result = ws.get_release_by_id("75b34c4a-1e15-3bf5-a734-abfafa94c731",["artist-credits","recordings","labels","isrcs","release-groups"])["release"]
print json.dumps(result, sort_keys=True, indent=4)
last_time = 0

PrintHeader()

filename_list = list()
for dirname, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if os.path.splitext(filename)[1] in ValidFileTypes: # Compares extension to valid extensions.
                filename_list.append(os.path.join(dirname,filename))
                num_total_songs += 1

DetectLibraryFolder(filename_list)
del filename_list

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
            if filename[-3:] == "mp3":
                try:
                    audio = (compatid3.CompatID3(dirname+"/"+filename),"mp3")
                except mutagen.id3.ID3NoHeaderError:
                    print ("Invalid MP3 File")
                else:
                    if audio[0].has_key("TXXX:musicbrainz_albumid"):
                        release_id = str(audio[0]["TXXX:musicbrainz_albumid"])
                    else:
                        if str(dirname+"/"+filename) not in skipped_files:
                            skipped_files.append(str(dirname+"/"+filename))

    #            print audio.pprint()
            elif filename[-4:] == "flac":
                try:
                    audio = (mutagen.flac.FLAC(dirname+"/"+filename),"flac")
                except mutagen.flac.FLACNoHeaderError:
                    print ("Invalid FLAC File")
                else:
                    if audio[0].has_key("musicbrainz_albumid"):
                        release_id = str(audio[0]["musicbrainz_albumid"][0])
                    else:
                        if str(dirname+"/"+filename) not in skipped_files:
                            skipped_files.append(str(dirname+"/"+filename))

    #            print audio.pprint()
            elif filename[-3:] == "ogg":
                audio = (mutagen.oggvorbis.OggVorbis(dirname+"/"+filename),"ogg")
                if audio[0].has_key("musicbrainz_albumid"):
                    release_id = str(audio[0]["musicbrainz_albumid"][0])
                else:
                    if str(dirname+"/"+filename) not in skipped_files:
                        skipped_files.append(str(dirname+"/"+filename))

#                print audio.pprint()

            if release_id != None:
                if (no_new_albums == False) or ((no_new_albums == True) and (release_id in albums.keys())):
                    result = RequestNextRelease(release_id)
                    if result is not None:
                        result.add_song(audio)
                        num_current_songs += 1

    while len(albums_fetch_queue) > 0:
        fetched_release = FetchNextRelease()
        if fetched_release != None:
            print "ID: " + fetched_release.id + " with " + str(len(fetched_release.songs)) + " songs."
            for s in fetched_release.songs:
                SyncMetadata(s,fetched_release)
            num_current_songs -= len(fetched_release.songs)
            print ("Pass {}: {} songs remaining to process and {}/{} processed.".format(num_passes, num_current_songs, num_processed_songs, num_total_songs))

    for album in albums.values():
        album.close()

    num_albums = len(albums)
    no_new_albums = False
    #print ("Albums processed: " + str(num_albums) + " Last Album Total: " + str(last_num_albums))

print ("\n-------------------------------------------------")
print ("Checked {} MP3s, {} OGGs and {} FLACs.".format(num_mp3s, num_oggs, num_flacs))
if len(skipped_files) > 0:
    print ("Skipped {} files with no MB Release ID:".format(len(skipped_files)))
    for s in skipped_files:
        print " " + s
