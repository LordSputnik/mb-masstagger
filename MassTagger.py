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
import mutagen.mp3
import mutagen.flac
import struct
import base64
from collections import defaultdict
from collections import deque
import musicbrainz2.webservice
import musicbrainzngs as ws
from utils import *
import json

num_flacs = num_mp3s = num_oggs = num_current_songs = num_processed_songs = num_total_songs = 0
albums_fetch_queue = deque()
albums = {}
songs = defaultdict(list)
skipped_files = list()
last_num_albums = None
num_albums = 0
num_passes = 0
no_new_albums = False
song_ids = list()
cover_art_list = {}

VorbisReleaseTags = {\
"artist-credit-phrase":u"albumartist",\
"asin":u"asin",\
"title":u"album",\
"barcode":u"barcode",\
"date":u"date",\
"country":u"releasecountry",\
}

VorbisRecordingTags = {\
"artist-credit-phrase":u"artist",\
"title":u"title",\
}

ws.set_rate_limit() #Disable the default rate limiting, as I do my own, and don't know whether this is blocking/non-blocking.
ws.set_useragent("mb-masstagger-py","0.1","ben.sput@gmail.com")
#q = musicbrainz2.webservice.Query(None,musicbrainz2.webservice.WebService,"masstagger-py-0.1")
#result = ws.get_release_by_id("75b34c4a-1e15-3bf5-a734-abfafa94c731",["artist-credits","recordings","labels","isrcs","release-groups"])["release"]
#print json.dumps(result, sort_keys=True, indent=4)
last_time = 0

def PrintHeader():
    print ("-------------------------------------------------")
    print ("| MusicBrainz Warp - 0.1                        |")
    print ("| Created Ben Ockmore AKA LordSputnik, (C) 2012 |")
    print ("-------------------------------------------------\n")
    print ("Starting...")
    return

def PackageCoverArt(image_content):
    pos = image_content.find(chr(255) + chr(0xC0))

    image_info = struct.unpack(">xxxxBHHB",image_content[pos:pos+10])

    #print "Image Size: " + str(len(image_content)) + " bytes"
    #print "Sample Precision: " + str(image_info[0])
    #print "Image Height: " + str(image_info[1])
    #print "Image Width: " + str(image_info[2])
    #print "Number of components: " + str(image_info[3])
    #print "Bits per Pixel: " + str(image_info[0]*image_info[3])
    return image_info[0],image_info[1],image_info[2],image_info[3],image_content


def FetchNextRelease():
    global last_time
    if (time.time() - last_time) < 1:
        return None

    last_time = time.time()
    if len(albums_fetch_queue) > 0:
        release_id = albums_fetch_queue.popleft()
        #print ("Fetching: |" + release_id + "| at time: {:.0f}.".format(time.time()))
        try:
            albums[release_id] = result = ws.get_release_by_id(release_id,["artist-credits","recordings","labels","isrcs","release-groups"])["release"]
        except musicbrainz2.webservice.WebServiceError as detail:
            print ("Web Service Error: " + str(detail))
            return None

        try:
            cover = urllib2.urlopen("http://coverartarchive.org/release/"+release_id+"/front-500",None,10)
        except urllib2.HTTPError:
            print "No cover art exists for "+release_id
            cover_art_list[release_id] = None
        else:
            cover_art_list[release_id] = PackageCoverArt(cover.read())

        return release_id
    else:
        return None

def RequestNextRelease(release_id):
    if release_id in albums:
        return release_id
    else:
        if release_id not in albums_fetch_queue:
            albums_fetch_queue.append(release_id)
        return None

###############################################
### Metadata Syncing Functions ################
###############################################

def GetVorbisCommentMetadata(song, release_id):
    release = albums[release_id]
    recording = None
    metadata = {}

    #Get the recording info for the song.
    for medium in release["medium-list"]:
        if medium["position"] == song["discnumber"][0]:
            for t in medium["track-list"]:
                if t["position"] == song["tracknumber"][0]:
                    recording = t["recording"]

    if recording is None: #Couldn't find the recording - we can't do anything (except maybe look for recording id).
        return None

    for key,value in release.items():
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
            metadata.setdefault(u"albumartistsort", []).append(aartist_sort_name)
        elif key == "status":
            metadata.setdefault(u"releasestatus", []).append(value.lower())
        elif key == "release-group":
            metadata.setdefault(u"originaldate", []).append(value["first-release-date"])
            metadata.setdefault(u"releasetype", []).append(value["type"].lower())

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
            metadata.setdefault(u"artistsort", []).append(artist_sort_name)
    
    return metadata

def SyncMP3MetaData(song,release_id):
    return

def SyncFLACMetaData(song,release_id):
    tags = GetVorbisCommentMetadata(song,release_id)
    
    cover_art = cover_art_list[release_id]
    if cover_art != None:
        song.clear_pictures();
        picture = mutagen.flac.Picture()
        picture.data = cover_art[4]
        picture.mime = "image/jpeg"
        picture.desc = ""
        picture.type = 3
        song.add_picture(picture)

    song.update(tags)
    song.save()

    os.rename(song.filename,"{:0>2}. {}{}".format(song[u"tracknumber"][0],song[u"title"][0],".flac"))
    
    print "Updating \"" + song[u"title"][0] + "\" by " + song["artist"][0]
    
    return

def SyncVorbisMetaData(song,release_id):
    tags = GetVorbisCommentMetadata(song,release_id)

    cover_art = cover_art_list[release_id]
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
    song.save()

    os.rename(song.filename,"{:0>2}. {}{}".format(song[u"tracknumber"][0],song[u"title"][0],".ogg"))

    print "Updating \"" + song[u"title"][0] + "\" by " + song["artist"][0]

    
    return

def SyncMetadata(song,release_id):
    global num_flacs, num_mp3s, num_oggs, num_processed_songs
    if albums[release_id] == None:
        return

    num_processed_songs += 1

    if "audio/mp3" in song.mime:
        num_mp3s += 1
        SyncMP3MetaData(song,release_id)
        #print song.pprint()
        #print ("Checking metadata for: " + str(song['TIT2']))
    elif "audio/x-flac" in song.mime:
        num_flacs += 1
        SyncFLACMetaData(song,release_id)
        #print ("Checking metadata for: " + song['title'][0])
    elif "audio/vorbis" in song.mime:
        num_oggs += 1
        SyncVorbisMetaData(song,release_id)
    else:
        print (str(song.mime))

    

    return

###############################################
### Main Script Loop ##########################
###############################################

PrintHeader()

for dirname, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if filename[-3:] == "mp3" or filename[-4:] == "flac" or filename[-3:] == "ogg":
                num_total_songs += 1

print ("Found {} songs to update.".format(num_total_songs))
print ("Updating...\n")

while num_albums != last_num_albums:
    last_num_albums = len(albums)
    num_passes += 1
    for dirname, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if (num_current_songs > 1000) or (len(cover_art_list) > 100):
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
                try:
                    audio = mutagen.mp3.MP3((dirname+"/"+filename))
                except mutagen.mp3.HeaderNotFoundError:
                    print ("Invalid MP3 File")
                else:
                    if audio.has_key("TXXX:musicbrainz_albumid"):
                        release_id = str(audio["TXXX:musicbrainz_albumid"])
                    else:
                        if str(dirname+"/"+filename) not in skipped_files:
                            skipped_files.append(str(dirname+"/"+filename))

    #            print audio.pprint()
            elif filename[-4:] == "flac":
                try:
                    audio = mutagen.flac.FLAC((dirname+"/"+filename))
                except mutagen.flac.FLACNoHeaderError:
                    print ("Invalid FLAC File")
                else:
                    if audio.has_key("musicbrainz_albumid"):
                        release_id = str(audio["musicbrainz_albumid"][0])
                    else:
                        if str(dirname+"/"+filename) not in skipped_files:
                            skipped_files.append(str(dirname+"/"+filename))

    #            print audio.pprint()
            elif filename[-3:] == "ogg":
                audio = mutagen.oggvorbis.OggVorbis(dirname+"/"+filename)
                if audio.has_key("musicbrainz_albumid"):
                    release_id = str(audio["musicbrainz_albumid"][0])
                else:
                    if str(dirname+"/"+filename) not in skipped_files:
                        skipped_files.append(str(dirname+"/"+filename))

#                print audio.pprint()

            if release_id != None:
                if (no_new_albums == False) or ((no_new_albums == True) and (release_id in albums_fetch_queue)):
                    if RequestNextRelease(release_id) == None:
                        songs[release_id].append(audio)
                        num_current_songs += 1
                    else:
                        SyncMetadata(audio,release_id)
                elif release_id in albums:
                    SyncMetadata(audio,release_id)

    while len(albums_fetch_queue) > 0:
        fetched_release = FetchNextRelease()
        if fetched_release != None:
            for s in songs[fetched_release]:
                SyncMetadata(s,fetched_release)
            num_current_songs -= len(songs[fetched_release])
            print ("Pass {}: {} songs remaining to process and {}/{} processed.".format(num_passes, num_current_songs, num_processed_songs, num_total_songs))
            del songs[fetched_release][:] #Clear the processed songs from this album
            albums[fetched_release] = None

    for key in albums.iterkeys():
        albums[key] = None


    num_albums = len(albums)
    no_new_albums = False
    #print ("Albums processed: " + str(num_albums) + " Last Album Total: " + str(last_num_albums))

print ("\n-------------------------------------------------")
print ("Checked {} MP3s, {} OGGs and {} FLACs.".format(num_mp3s, num_oggs, num_flacs))
if len(skipped_files) > 0:
    print ("Skipped {} files with no MB Release ID:".format(len(skipped_files)))
    for s in skipped_files:
        print " " + s


