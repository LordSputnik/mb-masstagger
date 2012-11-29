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
import musicbrainz2.webservice as ws

num_flacs = num_mp3s = num_oggs = num_current_songs = num_processed_songs = 0
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

#Gratefully Borrowed from MB Picard!
def sanitize_date(datestr):
    """Sanitize date format.

e.g.: "YYYY-00-00" -> "YYYY"
"YYYY- - " -> "YYYY"
...
"""
    date = []
    for num in datestr.split("-"):
        try:
            num = int(num.strip())
        except ValueError:
            break
        if num:
            date.append(num)
    return ("", "%04d", "%04d-%02d", "%04d-%02d-%02d")[len(date)] % tuple(date)

q = ws.Query(None,ws.WebService,"masstagger-py-0.1")
last_time = 0

def PackageCoverArt(image_content):
    pos = image_content.find(chr(255) + chr(0xC0))

    image_info = struct.unpack(">xxxxBHHB",image_content[pos:pos+10])

    
    print "Image Size: " + str(len(image_content)) + " bytes"
    print "Sample Precision: " + str(image_info[0])
    print "Image Height: " + str(image_info[1])
    print "Image Width: " + str(image_info[2])
    print "Number of components: " + str(image_info[3])
    print "Bits per Pixel: " + str(image_info[0]*image_info[3])
    return image_info[0],image_info[1],image_info[2],image_info[3],image_content
    

def FetchNextRelease():
    global last_time
    if (time.time() - last_time) < 1:
        return None
        
    last_time = time.time()
    if len(albums_fetch_queue) > 0:
        release_id = albums_fetch_queue.popleft()
        print ("Fetching: |" + release_id + "| at time: {:.0f}.".format(time.time()))
        try:
            albums[release_id] = q.getReleaseById(release_id)
        except ws.WebServiceError as detail:
            print ("Web Service Error: " + str(detail))
            return None
        
        try:
            cover = urllib2.urlopen("http://coverartarchive.org/release/"+release_id+"/front-500",None,10)
        except urllib2.HTTPError:
            print "No cover art exists for "+release_id
            cover_art_list[release_id] = None
        else:    
            cover_art_list[release_id] = PackageCoverArt(cover.read())
            
        print ("Fetched " + albums[release_id].getTitle())
        return release_id
    else:
        return None
        
def RequestNextRelease(release_id):
    if release_id in albums:
        return release_id
    else:
        if release_id not in albums_fetch_queue:
            albums_fetch_queue.append(release_id)
            print ("Added to fetch queue")
        return None

###############################################
### Metadata Syncing Functions ################
###############################################
def SyncMP3MetaData(song,release_id):
    return

def SyncFLACMetaData(song,release_id):
    release = albums[release_id]

    tags = {}
    tags.setdefault(u"albumartist", []).append(release.) #And here I decided to integrate into picard.
    
    cover_art = cover_art_list[release_id]
    if cover_art != None:
        song.clear_pictures();
        picture = mutagen.flac.Picture()
        picture.data = cover_art[4]
        picture.mime = "image/jpeg"
        picture.desc = ""
        picture.type = 3
        song.add_picture(picture)
    return

def SyncVorbisMetaData(song,release_id):
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

    song.save()
    
    return

###############################################
### Main Script Loop ##########################
###############################################

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
                print ("Pass " + str(num_passes) + ": " + str(num_current_songs) + " songs remaining to process and " + str(num_processed_songs) + " processed.")
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

                    if audio.has_key("metadata_block_picture"):
                        print "Len: "+str(len(audio['metadata_block_picture']))
    #            print audio.pprint()
            elif filename[-3:] == "ogg":
                audio = mutagen.oggvorbis.OggVorbis(dirname+"/"+filename)
                if audio.has_key("musicbrainz_albumid"):
                    release_id = str(audio["musicbrainz_albumid"][0])
                else:
                    if str(dirname+"/"+filename) not in skipped_files:
                        skipped_files.append(str(dirname+"/"+filename))
            
                print audio.pprint()

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
            print (fetched_release)
            for s in songs[fetched_release]:
                SyncMetadata(s,fetched_release)
            num_current_songs -= len(songs[fetched_release])
            print ("Pass " + str(num_passes) + ": " + str(num_current_songs) + " songs remaining to process and " + str(num_processed_songs) + " processed.")
            del songs[fetched_release][:] #Clear the processed songs from this album
            albums[fetched_release] = None

    print ("Noneing albums")
    for key in albums.iterkeys():
        albums[key] = None
       

    num_albums = len(albums)
    no_new_albums = False
    print ("Albums processed: " + str(num_albums) + " Last Album Total: " + str(last_num_albums))
        

print ("Checked {} MP3s, {} OGGs and {} FLACs.".format(num_mp3s, num_oggs, num_flacs))
if len(skipped_files) > 0:
    print ("Skipped {} files with no MB Release ID:".format(len(skipped_files)))
    for s in skipped_files:
        print " " + s


