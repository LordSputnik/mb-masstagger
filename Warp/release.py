import uuid
import urllib2
import struct

import musicbrainzngs as ws

import track

num_releases = 0

class Release:
    num_loaded = 0

    MetadataTags = {
        "artist-credit-phrase":"albumartist",
        "asin":"asin",
        "title":"album",
        "barcode":"barcode",
        "date":"date",
        "country":"releasecountry",
        "id":"musicbrainz_albumid"
    }

    def __init__(self,id_):
        self.songs = list()
        self.fetched = False
        self.valid = True
        self.art = None
        self.data = None
        self.processed_data = {}
        self.fetch_attempts = 0
        Release.num_loaded += 1
        try:
            uuid.UUID(id_)
        except ValueError:
            print "Corrupt UUID given."
            self.valid = False
        else:
            self.id = id_


    def Fetch(self):
        if not self.valid:
            return

        self.fetch_attempts += 1
        
        #Get the song metadata from MB Web Service - invalid release if this fails
        try:
            self.data = ws.get_release_by_id(self.id,["artist-credits","recordings","labels","release-groups","media"])["release"]
        except ws.musicbrainz.ResponseError:
            print ("Connection Error!")
            self.data = None
            return
        except ws.musicbrainz.NetworkError:
            print ("Connection Error!")
            self.data = None
            return

        self.__ProcessData()

        #Get cover art for release - no CA if this fails
        try:
            cover = urllib2.urlopen("http://coverartarchive.org/release/"+self.id+"/front-500",None,10)
        except urllib2.HTTPError:
            print "No cover art exists for " + self.id
            self.art = None
        except urllib2.URLError:
            print "Connection Error!"
            self.art = None
        else:
            self.art = self.__PackageCoverArt(cover.read())

        #Successfully retrieved data
        self.fetched = True
        return self.id

    def __ProcessData(self):
        for key,value in self.data.items():
            if key in self.MetadataTags:
                self.processed_data.setdefault(self.MetadataTags[key], []).append(value)
            elif key == "artist-credit":
                i = 0
                aartist_sort_name = ""
                for c in value:
                    if i == 0: #artist
                        aartist_sort_name += c["artist"]["sort-name"]
                        self.processed_data.setdefault("musicbrainz_albumartistid", []).append(c["artist"]["id"])
                    else: #join phrase
                        aartist_sort_name += c
                    i ^= 1
                self.processed_data.setdefault("albumartistsort", []).append(aartist_sort_name)
            elif key == "status":
                self.processed_data.setdefault("releasestatus", []).append(value.lower())
            elif key == "release-group":
                if "first-release-data" in value:
                    self.processed_data.setdefault("originaldate", []).append(value["first-release-date"])
                if "type" in value:
                    self.processed_data.setdefault("releasetype", []).append(value["type"].lower())
            elif key == "label-info-list":
                for label_info in value:
                    if "label" in label_info:
                        self.processed_data.setdefault("label", []).append(label_info["label"]["name"])
                    if "catalog-number" in label_info:
                        self.processed_data.setdefault("catalognumber", []).append(label_info["catalog-number"])
            elif key == "text-representation":
                if "language" in value:
                    self.processed_data.setdefault("language", []).append(value["language"])
                if "script" in value:
                    self.processed_data.setdefault("script", []).append(value["script"])

        self.processed_data.setdefault("totaldiscs", []).append(str(len(self.data["medium-list"])))

    def __PackageCoverArt(self,image_content):
        pos = image_content.find(chr(255) + chr(0xC0))

        image_info = struct.unpack(">xxxxBHHB",image_content[pos:pos+10])

        #print "Image Size: " + str(len(image_content)) + " bytes"
        #print "Sample Precision: " + str(image_info[0])
        #print "Image Height: " + str(image_info[1])
        #print "Image Width: " + str(image_info[2])
        #print "Number of components: " + str(image_info[3])
        #print "Bits per Pixel: " + str(image_info[0]*image_info[3])
        return image_info[0],image_info[1],image_info[2],image_info[3],image_content

    def Sync(self,options):
        if self.data is None:
            return

        for song in self.songs:
            song.inc_count()
            song.Sync(options)
            song.Save(options)

        return

    def AddSong(self,audio_file):
        if not self.valid:
            return

        track.Track.num_loaded += 1
        self.songs.append(audio_file)

    def Close(self):
        if self.valid:
            Release.num_loaded -= 1
            track.Track.num_loaded -= len(self.songs)
            self.valid = False
            self.data = None
            self.art = None
            del self.songs[:]
