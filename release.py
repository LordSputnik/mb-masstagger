import uuid
import urllib2
import struct
import musicbrainzngs as ws

class Release:
    def __init__(self,id_):
        self.valid = True
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

        #Do fetching here
        #try:
        self.data = ws.get_release_by_id(self.id,["artist-credits","recordings","labels","isrcs","release-groups"])["release"]
        #except musicbrainz2.webservice.WebServiceError as detail:
        #    print ("Web Service Error: " + str(detail))
        #    self.data = None

        try:
            cover = urllib2.urlopen("http://coverartarchive.org/release/"+self.id+"/front-500",None,10)
        except urllib2.HTTPError:
            print "No cover art exists for "+self.id
            self.art = None
        else:
            self.art = self.__PackageCoverArt(cover.read())

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
