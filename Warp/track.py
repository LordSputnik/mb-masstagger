import base64
import os
import copy
import sys
import unicodedata
import shutil

import mutagen.flac
import mutagen.id3
import mutagen.apev2

import utils
import compatid3
import script

class Track:
    num_loaded = 0
    num_processed = 0

    MetadataTags = {
        "artist-credit-phrase":"artist",
        "title":"title",
        "id":"musicbrainz_trackid"
    }

    def __init__(self,audio_file,file_ext,options):
        self.file = audio_file
        self.filename = ""

        self.directory = os.path.dirname(self.file.filename)


        self.ext = file_ext
        self.processed_data = {}
        self.discnumber = "0"
        self.tracknumber = "0"
        self.release = None
        self.ParseDiscAndTrackNumbers()

    def ParseDiscAndTrackNumbers(self):
        raise NotImplementedError

    def Sync(self,options):
        raise NotImplementedError

    def SaveFunc(self, options):
        raise NotImplementedError

    def Save(self, options):
        if self.processed_data is None:
            return

        Track.num_processed += 1

        self.SaveFunc(options)

        self._handle_filesystem_options(options)

        self.PostSave(options)

    def _script_to_filename(self, format_string, options):
        #Do format script replacing here.
        metadata = copy.copy(self.processed_data)
        
        filename = script.ScriptParser().eval(format_string, metadata, self)
        
        filename = filename.replace("\x00", "").replace("\t", "").replace("\n", "")

        # replace incompatible characters
        if options["windows_compatible_filenames"] or sys.platform == "win32":
            filename = utils.replace_win32_incompat(filename)

        if options["ascii_filenames"]:
            if isinstance(filename, unicode):
                filename = utils.unaccent(filename)
            filename = utils.replace_non_ascii(filename)

        return filename

    def _make_filename(self, options):
        """Constructs file name based on metadata and file naming formats."""
        if options["move_files"]:
            new_dirname = options["library_folder"]
            if not os.path.isabs(new_dirname):
                new_dirname = os.path.normpath(new_dirname)
        else:
            new_dirname = os.path.dirname(self.file.filename)

        new_filename, ext = os.path.splitext(os.path.basename(self.file.filename))

        if options["rename_files"]:

            format_string = options['rename_format']
            if len(format_string) > 0:

                new_filename = self._script_to_filename(format_string, options)

                if not options['move_files']:
                    new_filename = os.path.basename(new_filename)

                new_filename = utils.make_short_filename(new_dirname, new_filename)

                # win32 compatibility fixes
                if options['windows_compatible_filenames'] or sys.platform == 'win32':
                    new_filename = new_filename.replace('./', '_/').replace('.\\', '_\\')

                # replace . at the beginning of file and directory names
                new_filename = new_filename.replace('/.', '/_').replace('\\.', '\\_')

                if new_filename and new_filename[0] == '.':
                    new_filename = '_' + new_filename[1:]

                # Fix for precomposed characters on OSX
                if sys.platform == "darwin":
                    new_filename = unicodedata.normalize("NFD", unicode(new_filename))

        return os.path.realpath(os.path.join(new_dirname, new_filename + ext.lower()))

    def _rename(self, options):
        self.filename, ext = os.path.splitext(self._make_filename(options))
        if self.file.filename != self.filename + ext:
            new_dirname = os.path.dirname(self.filename)
            if not os.path.isdir(utils.encode_filename(new_dirname)):
                os.makedirs(new_dirname)
            tmp_filename = self.filename
            i = 1
            while (not utils.pathcmp(self.file.filename, self.filename + ext) and os.path.exists(utils.encode_filename(self.filename + ext))):
                self.filename = u"{} ({})".format(tmp_filename, i)
                i += 1
            self.filename = self.filename + ext
            common = os.path.commonprefix(list((os.path.dirname(self.file.filename),os.path.dirname(self.filename))))
            print utils.encode_filename(os.path.relpath(self.file.filename,common)) + "->" + utils.encode_filename(os.path.relpath(self.filename,common));
            shutil.move(utils.encode_filename(self.file.filename), utils.encode_filename(self.filename))
            return self.filename
        else:
            return self.file.filename

    def _handle_filesystem_options(self, options):
        """Save the metadata."""
        self.filename = self.file.filename
        # Rename files
        if options["rename_files"] or options["move_files"]:
            self.filename = self._rename(options)
        # Delete empty directories
        if options["delete_empty_dirs"]:
            dirname = utils.encode_filename(os.path.dirname(self.file.filename))
            try:
                self._rmdir(dirname)
                head, tail = os.path.split(dirname)
                if not tail:
                    head, tail = os.path.split(head)
                while head and tail:
                    try:
                        self._rmdir(head)
                    except:
                        break
                    head, tail = os.path.split(head)
            except EnvironmentError:
                pass
        return self.filename

    def _rmdir(self,dir_name):
        junk_files = (".DS_Store", "desktop.ini", "Desktop.ini", "Thumbs.db")
        if not set(os.listdir(dir_name)) - set(junk_files):
            shutil.rmtree(dir_name, False)
        else:
            raise OSError

    def PostSave(self,options):
        return

    def _ProcessData(self):
        if self.release is None:
            print "ERROR: Release is not set!"
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
                print "ERROR: Couldn't identify medium number!"
                self.processed_data = None
                return

        for medium in release_data["medium-list"]:
            if medium["position"] == self.discnumber:
                self.processed_data.setdefault("discnumber", []).append(self.discnumber)
                self.processed_data.setdefault("totaltracks", []).append(str(len(medium["track-list"])))

                if "format" in medium:
                    self.processed_data.setdefault("media", []).append(medium["format"])

                for t in medium["track-list"]:
                    if t["position"] == self.tracknumber:
                        self.processed_data.setdefault("tracknumber", []).append(self.tracknumber)
                        recording = t["recording"]

        if recording is None: #Couldn't find the recording - we can't do anything (except maybe look for recording id).
            print "ERROR: Couldn't identify recording in medium!"
            self.processed_data = None
            return

        for key,value in recording.items():

            if key in self.MetadataTags:
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

    id3encoding = 1 #use UTF-16 with BOM for now

    TranslationTable = {
        'comment'        : 'COMM',
        'albumartistsort': 'TSO2',
        'subtitle'       : 'TIT3',
        'lyricist'       : 'TEXT',
        'genre'          : 'TCON',
        'albumartist'    : 'TPE2',
        'composer'       : 'TCOM',
        'encodedby'      : 'TENC',
        'album'          : 'TALB',
        'mood'           : 'TMOO',
        'copyright'      : 'TCOP',
        'title'          : 'TIT2',
        'media'          : 'TMED',
        'label'          : 'TPUB',
        'artistsort'     : 'TSOP',
        'titlesort'      : 'TSOT',
        'discsubtitle'   : 'TSST',
        'website'        : 'WOAR',
        'remixer'        : 'TPE4',
        'conductor'      : 'TPE3',
        'compilation'    : 'TCMP',
        'language'       : 'TLAN',
        'date'           : 'TDRC',
        'isrc'           : 'TSRC',
        'originaldate'   : 'TDOR',
        'license'        : 'WCOP',
        'artist'         : 'TPE1',
        'bpm'            : 'TBPM',
        'albumsort'      : 'TSOA',
        'grouping'       : 'TIT1'
    }

    TranslateTextField = {
        'acoustid_fingerprint': 'Acoustid Fingerprint',
        'acoustid_id': 'Acoustid Id',
        'asin': 'ASIN',
        'barcode': 'BARCODE',
        'catalognumber': 'CATALOGNUMBER',
        'license': 'LICENSE',
        'musicbrainz_albumartistid': 'MusicBrainz Album Artist Id',
        'musicbrainz_albumid': 'MusicBrainz Album Id',
        'musicbrainz_artistid': 'MusicBrainz Artist Id',
        'musicbrainz_discid': 'MusicBrainz Disc Id',
        'musicbrainz_releasegroupid': 'MusicBrainz Release Group Id',
        'musicbrainz_trmid': 'MusicBrainz TRM Id',
        'musicbrainz_workid': 'MusicBrainz Work Id',
        'musicip_fingerprint': 'MusicMagic Fingerprint',
        'musicip_puid': 'MusicIP PUID',
        'releasecountry': 'MusicBrainz Album Release Country',
        'releasestatus': 'MusicBrainz Album Status',
        'releasetype': 'MusicBrainz Album Type',
        'script': 'SCRIPT'
    }

    #Tags which typically contain data stored in other tags.
    TagsToRemove = [
        "TXXX:musicbrainz_albumid",
        "TXXX:MUSICBRAINZ_ALBUMID",
        "TXXX:musicbrainz_artistid",
        "TXXX:MUSICBRAINZ_ARTISTID",
        "TXXX:musicbrainz_trackid",
        "TXXX:MUSICBRAINZ_TRACKID",
        "TXXX:musicbrainz_albumartistid",
        "TXXX:MUSICBRAINZ_ALBUMARTISTID",
        "TYER",
        "TDAT",
        "TIME"
    ]

    def inc_count(self):
        MP3Track.count += 1

    def ParseDiscAndTrackNumbers(self):
        if "TPOS" in self.file:
            self.discnumber = str(self.file["TPOS"][0]).partition("/")[0]

        if "TRCK" in self.file:
            self.tracknumber = str(self.file["TRCK"][0]).partition("/")[0]

    def SaveFunc(self, options):
        if options["id3version"] == "2.3":
            self.file.save(v1=0, v2=3)
        elif options["id3version"] == "2.4":
            self.file.save(v1=0, v2=4)

    def Sync(self,options):
        self._ProcessData()

        if self.processed_data == None:
            return

        tags = compatid3.CompatID3()

        for key,value in self.processed_data.items():
            if key in MP3Track.TranslationTable:
                tags.add(getattr(mutagen.id3,MP3Track.TranslationTable[key])(encoding=MP3Track.id3encoding, text=value[0]))
            elif key in MP3Track.TranslateTextField:
                tags.add(mutagen.id3.TXXX(encoding=MP3Track.id3encoding, desc=MP3Track.TranslateTextField[key], text=value[0]))
            elif key == "discnumber":
                tags.add(mutagen.id3.TPOS(encoding=0, text=value[0]+"/"+self.processed_data["totaldiscs"][0]))
            elif key == "tracknumber":
                tags.add(mutagen.id3.TRCK(encoding=0, text=value[0]+"/"+self.processed_data["totaltracks"][0]))
            elif key == "musicbrainz_trackid":
                tags.add(mutagen.id3.UFID(owner='http://musicbrainz.org', data=value[0]))

        if self.release.art != None:
            self.file.delall("APIC")
            tags.add(mutagen.id3.APIC(encoding=0, mime="image/jpeg", type=3, desc="", data=self.release.art[4]))

        if options["clear-tags"]:
            self.file.delete()
        else:
            for tag in MP3Track.TagsToRemove:
                if tag in self.file:
                    del self.file[tag]

        self.file.update(tags)

        if options["id3version"] == "2.3":
            self.file.update_to_v23()
        elif options["id3version"] == "2.4":
            self.file.update_to_v24()

        print "Updating \"" + unicode(self.file[MP3Track.TranslationTable["title"]].text[0]).encode("ascii","ignore") + "\" by " + unicode(self.file[MP3Track.TranslationTable["artist"]].text[0]).encode("ascii","ignore")

    def PostSave(self,options):
        if options["remove-ape"]:
            mutagen.apev2.delete(self.filename)

class FLACTrack(Track):

    count = 0

    def inc_count(self):
        FLACTrack.count += 1

    def ParseDiscAndTrackNumbers(self):
        if "discnumber" in self.file:
            self.discnumber = str(self.file["discnumber"][0])

        if "tracknumber" in self.file:
            self.tracknumber = str(self.file["tracknumber"][0])

    def SaveFunc(self, options):
        self.file.save()

    def Sync(self,options):
        self._ProcessData()

        if self.processed_data == None:
            return

        tags = {}

        for key,value in self.processed_data.items():
            tags[key.upper().encode("utf-8")] = value

        cover_art = self.release.art

        if options["clear-tags"]:
            self.file.delete()

        if cover_art != None:
            self.file.clear_pictures();
            picture = mutagen.flac.Picture()
            picture.data = cover_art[4]
            picture.mime = "image/jpeg"
            picture.desc = ""
            picture.type = 3
            self.file.add_picture(picture)

        self.file.update(tags)

        print "Updating \"" + unicode(self.file[u"title"][0]).encode("ascii","ignore") + "\" by " + unicode(self.file["artist"][0]).encode("ascii","ignore")


class OggTrack(Track):

    count = 0

    def inc_count(self):
        OggTrack.count += 1

    def ParseDiscAndTrackNumbers(self):
        if "discnumber" in self.file:
            self.discnumber = str(self.file["discnumber"][0])

        if "tracknumber" in self.file:
            self.tracknumber = str(self.file["tracknumber"][0])

    def SaveFunc(self, options):
        self.file.save()

    def Sync(self,options):
        self._ProcessData()

        if self.processed_data == None:
            return

        tags = {}

        for key,value in self.processed_data.items():
            tags[key.upper().encode("utf-8")] = value

        cover_art = self.release.art

        if options["clear-tags"]:
            self.file.delete()

        if cover_art != None:

            if u"METADATA_BLOCK_PICTURE" in self.file:
                self.file[u"METADATA_BLOCK_PICTURE"] = []

            picture = mutagen.flac.Picture()
            picture.data = cover_art[4]
            picture.mime = "image/jpeg"
            picture.desc = ""
            picture.type = 3
            tags.setdefault(u"METADATA_BLOCK_PICTURE", []).append(base64.standard_b64encode(picture.write()))

        self.file.update(tags)

        print "Updating \"" + unicode(self.file[u"title"][0]).encode("ascii","ignore") + "\" by " + unicode(self.file["artist"][0]).encode("ascii","ignore")
