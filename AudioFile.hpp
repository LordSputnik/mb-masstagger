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

#ifndef _MBMT_AUDIOFILE_H_
#define _MBMT_AUDIOFILE_H_

#include "pch.hpp"

namespace MassTagger
{
    enum AudioFileType
    {
        AUDIO_FLAC = 0,
        AUDIO_MP3,
        AUDIO_VORBIS,
        AUDIO_UNKNOWN
    };

    class AudioFile
    {
        struct Tags
        {
          //Artist, ids, etc. go here.
          //Unicode Strings
          TagLib::String title_;
          TagLib::String release_name_;
          TagLib::String artist_name_;

          //ASCII strings
          std::string recording_uuid_;
          std::string release_uuid_;
          std::string artist_uuid_;
        };

        private:
        AudioFileType type_;
        std::string path_;
        Tags retrieved_tags_;
        Tags stored_tags_;

        public:
        AudioFile(const boost::filesystem::path & path, AudioFileType type = AUDIO_UNKNOWN);
        void GetTags();
        uint8_t type() const
        {
            return type_;
        }

        std::string & path()
        {
            return path_;
        }

        static AudioFileType GetAudioFileType(const boost::filesystem::path & path);
    };
}

#endif // _MBMT_AUDIOFILE_H_
