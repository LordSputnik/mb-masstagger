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
import release

from utils import *

num_flacs = num_mp3s = num_oggs = num_current_songs = num_processed_songs = num_total_songs = 0

library_folder = ""

albums_fetch_queue = deque()
albums = {}
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

VorbisReleaseTags = {
    "artist-credit-phrase":"albumartist",
    "asin":"asin",
    "title":"album",
    "barcode":"barcode",
    "date":"date",
    "country":"releasecountry",
}

VorbisRecordingTags = {
    "artist-credit-phrase":"artist",
    "title":"title",
}

def DetectLibraryFolder(filenames):
    global library_folder

    possible_library_folder = os.path.commonprefix(filenames)
    if os.path.isdir(possible_library_folder):
        library_folder = possible_library_folder


def PrintHeader():
    print ("\
-------------------------------------------------\n\
| MusicBrainz Warp - 0.1                        |\n\
| Created Ben Ockmore AKA LordSputnik, (C) 2012 |\n\
-------------------------------------------------\n\n\
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
            return release_id
        else:
            return None
    else:
        return None

def RequestNextRelease(release_id):
    global albums
    if release_id not in albums:
        if release_id not in albums_fetch_queue:
            albums_fetch_queue.append(release_id)
            albums[release_id] = release.Release(release_id)

    return albums[release_id]

###############################################
### Metadata Syncing Functions ################
###############################################

def SaveFile(audio_file, disc_num, track_num, title, ext):
    audio_file.save()
    os.rename(audio_file.filename,os.path.join(library_folder,"{:0>2}. {}{}".format(track_num,title,ext)))

def GetVorbisCommentMetadata(song, release_id):
    release_data = albums[release_id].data
    recording = None
    metadata = {}

    #Get the recording info for the song.
    for medium in release_data["medium-list"]:
        if medium["position"] == song["discnumber"][0]:
            for t in medium["track-list"]:
                if t["position"] == song["tracknumber"][0]:
                    recording = t["recording"]

    if recording is None: #Couldn't find the recording - we can't do anything (except maybe look for recording id).
        return None

    for key,value in release_data.items():
        if VorbisReleaseTags.has_key(key):
            metadata.setdefault(VorbisReleaseTags[key], []).append(value)
        elif key == "artist-credit":
            i = 0
            aartist_sort_name = ""
            for c in value:
                if i == 0: #artist
                    aartist_sort_name += c["artist"]["sort-name"]
                else: #join phrase
                    aartist_sort_name += c
                i ^= 1
            metadata.setdefault("albumartistsort", []).append(aartist_sort_name)
        elif key == "status":
            metadata.setdefault("releasestatus", []).append(value.lower())
        elif key == "release-group":
            metadata.setdefault("originaldate", []).append(value["first-release-date"])
            metadata.setdefault("releasetype", []).append(value["type"].lower())

    for key,value in recording.items():
        if VorbisRecordingTags.has_key(key):
            metadata.setdefault(VorbisRecordingTags[key], []).append(value)
        elif key == "artist-credit":
            i = 0
            artist_sort_name = ""
            for c in value:
                if i == 0: #artist
                    artist_sort_name += c["artist"]["sort-name"]
                else: #join phrase
                    artist_sort_name += c
                i ^= 1
            metadata.setdefault("artistsort", []).append(artist_sort_name)

    return metadata

def SyncMP3MetaData(song,release_id):
    return

def SyncFLACMetaData(song,release_id):
    metadata = GetVorbisCommentMetadata(song,release_id)
    tags = {}

    for key,value in metadata.items():
        tags[key.upper().encode("utf-8")] = value

    cover_art = albums[release_id].art
    if cover_art != None:
        song.clear_pictures();
        picture = mutagen.flac.Picture()
        picture.data = cover_art[4]
        picture.mime = "image/jpeg"
        picture.desc = ""
        picture.type = 3
        song.add_picture(picture)

    song.update(tags)
    SaveFile(song,1,song[u"tracknumber"][0],song[u"title"][0],".flac")

    print "Updating \"" + song[u"title"][0] + "\" by " + song["artist"][0]

    return

def SyncVorbisMetaData(song,release_id):
    metadata = GetVorbisCommentMetadata(song,release_id)
    tags = {}

    for key,value in metadata.items():
        tags[key.upper().encode("utf-8")] = value

    cover_art = albums[release_id].art
    if cover_art != None:
        if song.has_key(u"METADATA_BLOCK_PICTURE"):
            song[u"METADATA_BLOCK_PICTURE"] = []
        picture = mutagen.flac.Picture()
        picture.data = cover_art[4]
        picture.mime = "image/jpeg"
        picture.desc = ""
        picture.type = 3
        tags.setdefault(u"METADATA_BLOCK_PICTURE", []).append(base64.standard_b64encode(picture.write()))

    song.update(tags)
    SaveFile(song,1,song[u"tracknumber"][0],song[u"title"][0],".ogg")

    print "Updating \"" + song[u"title"][0] + "\" by " + song["artist"][0]


    return

def SyncMetadata(song,release_id):
    global num_flacs, num_mp3s, num_oggs, num_processed_songs

    if not albums[release_id].valid:
        return

    num_processed_songs += 1

    if song[1] == "mp3":
        num_mp3s += 1
        SyncMP3MetaData(song[0],release_id)
    elif song[1] == "flac":
        num_flacs += 1
        SyncFLACMetaData(song[0],release_id)
    elif song[1] == "ogg":
        num_oggs += 1
        SyncVorbisMetaData(song[0],release_id)
    else:
        num_processed_songs -= 1

    return

###############################################
### Main Script Loop ##########################
###############################################

ws.set_rate_limit() #Disable the default rate limiting, as I do my own, and don't know whether this is blocking/non-blocking.
ws.set_useragent("mb-masstagger-py","0.1","ben.sput@gmail.com")

#result = ws.get_release_by_id("75b34c4a-1e15-3bf5-a734-abfafa94c731",["artist-credits","recordings","labels","isrcs","release-groups"])["release"]
#print json.dumps(result, sort_keys=True, indent=4)
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

            fetched_release = FetchNextRelease()
            if fetched_release != None:
                for s in songs[fetched_release]:
                    SyncMetadata(s,fetched_release)
                num_current_songs -= len(songs[fetched_release])
                print ("Pass {}: {} songs remaining to process and {}/{} processed.".format(num_passes, num_current_songs, num_processed_songs, num_total_songs))
                del songs[fetched_release][:] #Clear the processed songs from this album

            release_id = None
            audio = None
            if filename[-3:] == "mp3":
#                try:
                audio = (compatid3.CompatID3(dirname+"/"+filename),"mp3")
                #except mutagen.mp3.HeaderNotFoundError:
                #    print ("Invalid MP3 File")
                #else:
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
                if release_id in albums and albums[release_id].fetched:
                    SyncMetadata(audio,release_id)
                elif (no_new_albums == False) or ((no_new_albums == True) and (release_id in albums_fetch_queue)):
                    result = RequestNextRelease(release_id)
                    songs[release_id].append(audio)
                    result.add_song(audio)
                    num_current_songs += 1

    while len(albums_fetch_queue) > 0:
        fetched_release = FetchNextRelease()
        if fetched_release != None:
            for s in songs[fetched_release]:
                SyncMetadata(s,fetched_release)
            num_current_songs -= len(songs[fetched_release])
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
