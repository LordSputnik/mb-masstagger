import uuid
import urllib2
import struct
import musicbrainzngs as ws

class Release:
    
    def __init__(self,id_):
        self.songs = list()
        self.fetched = False
        self.valid = True
        self.art = None
        self.data = None
        try:
            uuid.UUID(id_)
        except ValueError:
            print "Corrupt UUID given."
            self.valid = False
        else:
            self.id = id_
            

    def fetch(self):
        if not self.valid:
            return

        #Get the song metadata from MB Web Service - invalid release if this fails
        try:
            self.data = ws.get_release_by_id(self.id,["artist-credits","recordings","labels","isrcs","release-groups"])["release"]
        except ws.musicbrainz.ResponseError:
            print ("Connection Error!")
            self.data = None
            return
        except ws.musicbrainz.NetworkError:
            print ("Connection Error!")
            self.data = None
            return

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

    def add_song(self,audio_file):
        if not self.valid:
            return

        self.songs.append(audio_file)

    def close(self):
        if self.valid:
            self.valid = False
            self.data = None
            self.art = None
            del self.songs[:]
