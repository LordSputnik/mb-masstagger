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

namespace MassTagger
{
    AudioFile::AudioFile(const boost::filesystem::path & path, AudioFileType type)
        : path_(path.native())
    {
        if(type == AUDIO_UNKNOWN)
            type_ = GetAudioFileType(path);
        else
            type_ = type;
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

    }
}