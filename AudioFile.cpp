/*
 * Copyright (C) 2012 Ben Ockmore
 *
 * This file is part of MusicBrainz MassTagger.
 *
 * MusicBrainz MassTagger is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * MusicBrainz MassTagger is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with MusicBrainz MassTagger.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "AudioFile.hpp"
#include "App.hpp"

using std::cout;
using std::endl;

namespace MassTagger
{
    bool AudioFile::Tags::SyncTag(const std::string & tag_name, const std::string & value)
    {
      if((*this)(tag_name) == value)
        return true;

      cout << tag_name << ": " << (*this)(tag_name) << "->" << value << endl;
      (*this)(tag_name) = value;
      return false;
    }

    bool AudioFile::Tags::SyncTag(const std::string & tag_name, int value)
    {
      if((*this)[tag_name] == value)
        return true;

      cout << tag_name << ": " << (*this)[tag_name] << "->" << value << endl;
      (*this)[tag_name] = value;
      return false;
    }

    AudioFile::AudioFile(const boost::filesystem::path & path, AudioFileType type)
        : path_(path.native())
    {
        if(type == AUDIO_UNKNOWN)
            type_ = GetAudioFileType(path);
        else
            type_ = type;

        GetTags();
    }

    AudioFileType AudioFile::GetAudioFileType(const boost::filesystem::path & path)
    {
        boost::filesystem::path extension = path.extension();
        const std::string & ext = extension.native(); //For some reason path.extension().native() doesn't work 0o

        // No audio files with less than 2 characters in extension (.wv needs to be supported).
        if(ext.length() < 2)
        {
            return AUDIO_UNKNOWN;
        }

        if((ext.compare(1,4,"flac") == 0) || (ext.compare(1,4,"FLAC") == 0))
        {
            return AUDIO_FLAC;
        }
        else if((ext.compare(1,3,"mp3") == 0) || (ext.compare(1,3,"MP3") == 0))
        {
            return AUDIO_MP3;
        }
        else if((ext.compare(1,3,"ogg") == 0) || (ext.compare(1,3,"OGG") == 0))
        {
            return AUDIO_VORBIS;
        }

        return AUDIO_UNKNOWN;
    }

    void AudioFile::GetTags()
    {
      TagLib::FileRef f(path_.c_str());
      stored_tags_("ARTIST") = f.tag()->artist().to8Bit(true);
      stored_tags_("RELEASE") = f.tag()->album().to8Bit(true);
      stored_tags_("TITLE") = f.tag()->title().to8Bit(true);
      stored_tags_["TRACK_INDEX"] = f.tag()->track() - 1;

      TagLib::PropertyMap pmap = f.file()->properties();

      TagLib::PropertyMap::Iterator it = pmap.begin(), end = pmap.end();
      for(; it != end; ++it)
      {
        if(it->first == "MUSICBRAINZ_TRACKID")
          stored_tags_("REC_ID") = it->second[0].to8Bit();
        else
        if(it->first == "MUSICBRAINZ_ALBUMID")
          stored_tags_("REL_ID") = it->second[0].to8Bit();
        else
        if(it->first == "MUSICBRAINZ_ARTISTID")
          stored_tags_("ARTIST_ID") = it->second[0].to8Bit();
        else
        if(it->first == "DATE")
          stored_tags_("DATE") = it->second[0].to8Bit();
        else
        if(it->first == "ORIGINALDATE")
          stored_tags_("ORIGINALDATE") = it->second[0].to8Bit();
        else
        if(it->first == "DISCNUMBER")
        {
          std::stringstream ss(it->second[0].to8Bit());
          ss >> stored_tags_["DISC_INDEX"];
          --stored_tags_["DISC_INDEX"]; //1->X -> 0->X-1
        }
      }

      CheckTags();
    }

    void AudioFile::CheckTags()
    {
      if(stored_tags_("REL_ID").empty() == true)
        return;

      MusicBrainz5::CRelease* release = App::LookupReleaseID(stored_tags_("REL_ID"));

      if(release == nullptr)
        return;

      MusicBrainz5::CTrack* track = release->MediumList()->Item(stored_tags_["DISC_INDEX"])->TrackList()->Item(stored_tags_["TRACK_INDEX"]);

      bool changed = false;

      stored_tags_.SyncTag("RELEASE", release->Title());
      stored_tags_.SyncTag("TITLE", track->Recording()->Title());
      stored_tags_.SyncTag("DATE",release->Date());
      stored_tags_.SyncTag("ORIGINALDATE",release->ReleaseGroup()->FirstReleaseDate());
      stored_tags_.SyncTag("REC_ID",track->Recording()->ID());
    }
}
