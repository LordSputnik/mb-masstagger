import uuid
import urllib2
import struct
import musicbrainzngs as ws
import copy
import mutagen.oggvorbis
import mutagen.flac
import compatid3
import base64

class Track:
    MetadataTags = {
        "artist-credit-phrase":"artist",
        "title":"title",
        "id":"musicbrainz_trackid"
    }

    def __init__(self,audio_file,type):
        self.file = audio_file
        self.ext = type
        self.processed_data = {}
        self.discnumber = "0"
        self.tracknumber = "0"
        self.release = None

        if audio_file.has_key("discnumber"):
            self.discnumber = str(audio_file["discnumber"][0])

        if audio_file.has_key("tracknumber"):
            self.tracknumber = str(audio_file["tracknumber"][0])

    def Sync(self):
        raise NotImplementedError

    def Save(self, options):
        if self.processed_data is None:
            return

        self.file.save()

        dest_name = ""
        disc_string = "{"+":0>{}".format(len(self.processed_data["totaldiscs"][0])) + "}"
        track_string = "{"+":0>{}".format(len(self.processed_data["totaltracks"][0])) + "}"

        if options["rename-files"]:
            if int(self.processed_data["totaldiscs"][0]) == 1:
                dest_name = options["rename-format"]
            else:
                dest_name = options["multi-disc-rename-format"]

            dest_name = dest_name.replace("D",disc_string.format(self.discnumber)).replace("#",track_string.format(self.tracknumber)).replace("T","{}.{}".format(self.processed_data["title"][0],self.ext))
            print dest_name

            os.rename(self.file.filename,os.path.join(options["library-folder"],dest_name))

    def _ProcessData(self):
        if self.release is None:
            self.processed_data = None
            return

        release_data = self.release.data
        recording = None
        self.processed_data = copy.copy(self.release.processed_data)

        #Get the recording info for the song.
        total_discs = len(release_data["medium-list"])

        #TODO - Move this out of the function so that we can specialize to the correct tag for each file format. Perhaps put in Song class.
        if self.discnumber == "0":
            if total_discs == 1:
                self.discnumber = "1"
            else:
                print "Error, no disc number for multi-disc release!"
                self.processed_data = None
                return

        self.processed_data.setdefault("totaldiscs", []).append(str(len(release_data["medium-list"])))
        for medium in release_data["medium-list"]:

            if medium["position"] == self.discnumber:
                self.processed_data.setdefault("discnumber", []).append(self.discnumber)
                self.processed_data.setdefault("totaltracks", []).append(str(len(medium["track-list"])))

                for t in medium["track-list"]:

                    if t["position"] == self.tracknumber:
                        self.processed_data.setdefault("tracknumber", []).append(self.tracknumber)
                        recording = t["recording"]

        if recording is None: #Couldn't find the recording - we can't do anything (except maybe look for recording id).
            self.processed_data = None
            return

        for key,value in recording.items():

            if self.MetadataTags.has_key(key):
                self.processed_data.setdefault(self.MetadataTags[key], []).append(value)

            elif key == "artist-credit":
                i = 0
                artist_sort_name = ""
                for c in value:
                    if i == 0: #artist
                        artist_sort_name += c["artist"]["sort-name"]
                        self.processed_data.setdefault("musicbrainz_artistid", []).append(c["artist"]["id"])
                    else: #join phrase
                        artist_sort_name += c
                    i ^= 1
                self.processed_data.setdefault("artistsort", []).append(artist_sort_name)
        return

class MP3Track(Track):

    count = 0

    def inc_count(self):
        return
        #MP3Track.count += 1

    def Sync(self,options):
        #self._ProcessData()
        self.processed_data = None
        print "\nMP3"

class FLACTrack(Track):

    count = 0

    def inc_count(self):
        FLACTrack.count += 1

    def Sync(self,options):
        self._ProcessData()

        if self.processed_data == None:
            return

        tags = {}

        if options["clear-tags"]:
            self.file.delete()

        for key,value in self.processed_data.items():
            tags[key.upper().encode("utf-8")] = value

        cover_art = self.release.art

        if cover_art != None:
            self.file.clear_pictures();
            picture = mutagen.flac.Picture()
            picture.data = cover_art[4]
            picture.mime = "image/jpeg"
            picture.desc = ""
            picture.type = 3
            self.file.add_picture(picture)

        self.file.update(tags)

        print "Updating \"" + self.file[u"title"][0] + "\" by " + self.file["artist"][0]


class OggTrack(Track):

    count = 0

    def inc_count(self):
        OggTrack.count += 1

    def Sync(self,options):
        self._ProcessData()

        if self.processed_data == None:
            return

        tags = {}

        if options["clear-tags"]:
            self.file.delete()

        for key,value in self.processed_data.items():
            tags[key.upper().encode("utf-8")] = value

        cover_art = self.release.art
        if cover_art != None:

            if self.file.has_key(u"METADATA_BLOCK_PICTURE"):
                self.file[u"METADATA_BLOCK_PICTURE"] = []

            picture = mutagen.flac.Picture()
            picture.data = cover_art[4]
            picture.mime = "image/jpeg"
            picture.desc = ""
            picture.type = 3
            tags.setdefault(u"METADATA_BLOCK_PICTURE", []).append(base64.standard_b64encode(picture.write()))

        self.file.update(tags)

        print "Updating \"" + self.file[u"title"][0] + "\" by " + self.file["artist"][0]

class Release:
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
            if self.MetadataTags.has_key(key):
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
                self.processed_data.setdefault("originaldate", []).append(value["first-release-date"])
                self.processed_data.setdefault("releasetype", []).append(value["type"].lower())

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
