# -*- coding: utf-8 -*-

# Copyright (C) 2013 Ben Ockmore

# This file is part of Warp Tagger.

# Warp Tagger is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# Warp Tagger is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Warp Tagger. If not, see <http://www.gnu.org/licenses/>.

import uuid
import urllib2
import struct

import musicbrainzngs as ws

import track
import utils
import metadata
import socket

num_releases = 0

class Release:
    num_loaded = 0

    MetadataTags = {
        "asin":"asin",
        "title":"album",
        "date":"date",
        "country":"releasecountry",
        "id":"musicbrainz_albumid"
    }

    def __init__( self, id_ ):
        self.songs = list()
        self.fetched = False
        self.valid = True
        self.art = None
        self.data = None
        self.processed_data = metadata.Metadata()
        self.fetch_attempts = 0
        Release.num_loaded += 1
        try:
            uuid.UUID( id_ )
        except ValueError:
            utils.safeprint( u"Corrupt UUID in file." )
            self.valid = False
        else:
            self.id = id_


    def Fetch( self, options ):
        if not self.valid:
            return

        self.fetch_attempts += 1

        # Get the song metadata from MB Web Service - invalid release if this fails
        try:
            self.data = ws.get_release_by_id( self.id, ["artist-credits", "recordings", "labels", "release-groups", "media"] )["release"]
        except ws.musicbrainz.ResponseError:
            utils.safeprint ( u"Connection Error!" )
            self.data = None
            return
        except ws.musicbrainz.NetworkError:
            utils.safeprint ( u"Connection Error!" )
            self.data = None
            return

        self.__ProcessData( options )

        # Get cover art for release - no CA if this fails
        try:
            cover = urllib2.urlopen( "http://coverartarchive.org/release/" + self.id + "/front-500", None, 10 )
        except urllib2.HTTPError:
            utils.safeprint( u"No cover art in CAA for \"{}\".".format( self.processed_data["album"] ) )
            self.art = None
        except ( urllib2.URLError, socket.timeout ):
            utils.safeprint( u"Connection Error!" )
            self.art = None
        else:
            self.art = self.__PackageCoverArt( cover.read() )

        # Successfully retrieved data
        self.fetched = True
        return self.id

    def __ProcessData( self, options ):
        for key, value in self.data.items():
            if key in self.MetadataTags:
                self.processed_data.add( self.MetadataTags[key], value )
            elif key == "artist-credit":
                i = 0
                aartist_sort_name = u""
                aartist_credit = u""
                for c in value:
                    if i == 0:  # artist
                        if options["use_standard_artist_names"] or ( "name" not in c ):
                            aartist_credit += c["artist"]["name"]
                        else:
                            aartist_credit += c["name"]

                        aartist_sort_name += c["artist"]["sort-name"]
                        self.processed_data.add( "musicbrainz_albumartistid", c["artist"]["id"] )
                    else:  # join phrase
                        aartist_sort_name += c
                        aartist_credit += c
                    i ^= 1
                self.processed_data.add( "albumartistsort", aartist_sort_name )
                self.processed_data.add( "albumartist", aartist_credit )
            elif key == "status":
                self.processed_data.add( "releasestatus", value.lower() )
            elif key == "release-group":
                if "first-release-date" in value:
                    self.processed_data.add( "originaldate", value["first-release-date"] )
                if "type" in value:
                    self.processed_data.add( "releasetype", value["type"].lower() )
            elif key == "label-info-list":
                for label_info in value:
                    if "label" in label_info:
                        self.processed_data.add( "label", label_info["label"]["name"] )
                    if "catalog-number" in label_info:
                        self.processed_data.add( "catalognumber", label_info["catalog-number"] )
            elif key == "barcode":
                if value is not None:
                    self.processed_data.add( "barcode", value )
            elif key == "text-representation":
                if "language" in value:
                    self.processed_data.add( "language", value["language"] )
                if "script" in value:
                    self.processed_data.add( "script", value["script"] )

        self.processed_data.add( "totaldiscs", str( len( self.data["medium-list"] ) ) )

        run_album_metadata_processors( None, self.processed_data, self.data )

    def __PackageCoverArt( self, image_content ):
        pos = image_content.find( chr( 255 ) + chr( 0xC0 ) )

        image_info = struct.unpack( ">xxxxBHHB", image_content[pos:pos + 10] )

        # print "Image Size: " + str(len(image_content)) + " bytes"
        # print "Sample Precision: " + str(image_info[0])
        # print "Image Height: " + str(image_info[1])
        # print "Image Width: " + str(image_info[2])
        # print "Number of components: " + str(image_info[3])
        # print "Bits per Pixel: " + str(image_info[0]*image_info[3])
        return image_info[0], image_info[1], image_info[2], image_info[3], image_content

    def Sync( self, options ):
        if self.data is None:
            return

        utils.safeprint( u"Updating {} by {}...".format( self.processed_data["album"], self.processed_data["albumartist"] ) )

        for song in self.songs:
            song.inc_count()
            song.Sync( options )
            song.Save( options )

        return

    def AddSong( self, audio_file ):
        if not self.valid:
            return

        track.Track.num_loaded += 1
        self.songs.append( audio_file )

    def Close( self ):
        if self.valid:
            Release.num_loaded -= 1
            track.Track.num_loaded -= len( self.songs )
            self.valid = False
            self.data = None
            self.art = None
            del self.songs[:]

_album_metadata_processors = []

def register_album_metadata_processor( function ):
    """Registers new album-level metadata processor."""
    _album_metadata_processors.append( function )

def run_album_metadata_processors( tagger, metadata, release ):
    for processor in _album_metadata_processors:
        processor( tagger, metadata, release )
