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

#include <iostream>
#include <taglib/taglib.h>
#include <taglib/fileref.h>
#include <taglib/tpropertymap.h>

#include <musicbrainz5/Query.h>
#include <musicbrainz5/Disc.h>
#include <musicbrainz5/Release.h>
#include <musicbrainz5/Recording.h>

#include <boost/filesystem.hpp>
#include <boost/version.hpp>
#include <list>
#include <vector>
#include <memory>
#include "AudioFile.hpp"
using namespace std;

list<std::shared_ptr<MassTagger::AudioFile>> music_files;

uint32_t num_mp3s = 0, num_flacs = 0, num_oggs = 0;

void ScanDirectory(const boost::filesystem::path & input_dir)
{
    boost::filesystem::directory_iterator it(input_dir);
    boost::filesystem::directory_iterator end;
    for(;it != end; ++it)
    {
        if(is_directory(*it) == true)
        {
            ScanDirectory(*it);
            continue;
        }

        if(is_regular_file(*it) == false)
            continue;

        MassTagger::AudioFileType type = MassTagger::AudioFile::GetAudioFileType(*it);

        if(type == MassTagger::AUDIO_UNKNOWN)
            continue;

        if(type == MassTagger::AUDIO_FLAC)
            ++num_flacs;
        else if(type == MassTagger::AUDIO_MP3)
            ++num_mp3s;
        else if (type == MassTagger::AUDIO_VORBIS)
            ++num_oggs;

        std::shared_ptr<MassTagger::AudioFile> ptr (new MassTagger::AudioFile(*it,type));
        music_files.push_back(ptr);
    }
}

int main()
{
    /* So, what stuff regularly needs updating in my library? Everything? No...
    * Recording
    *   Artist Name
    *   Album Name
    * Release
    *   Album Art -> libcoverart
    *   Release Date
    *   Original Release Date
    *   Track Number/Total
    *   Disc Number/Total
    *   Country
    * Work
    *   Composer
    */

    boost::filesystem::path root_dir ("./");
    std::cout << "Boost version: " << BOOST_LIB_VERSION << std::endl;
    if(exists(root_dir))
    {
        cout << "This should always exist, probably." << endl;
        ScanDirectory(root_dir);

    }

    printf("Found %u MP3s, %u OGGs and %u FLACs.\n",num_mp3s,num_oggs,num_flacs);

    /*
    TagLib::FileRef f("Spirits.flac");
    TagLib::String artist = f.tag()->title(); // artist == "Frank Zappa"
    TagLib::PropertyMap pmap = f.file()->properties();

    TagLib::PropertyMap::Iterator it = pmap.begin();
    auto end = pmap.end();

    for(;it != end; ++it)
    {
        cout << it->first << " " << it->second << endl;
    }

    it = pmap.find("MUSICBRAINZ_TRACKID");
    TagLib::String release_id = it->second[0];
    cout << "Release Id:" << release_id << endl;
    MusicBrainz5::CQuery Query("release-lookup");
    MusicBrainz5::CQuery::tParamMap Params;
    //Params["inc"]="artists labels recordings release-groups url-rels discids artist-credits";
    MusicBrainz5::CMetadata Metadata =Query.Query("recording",release_id.to8Bit());
    if (Metadata.Recording())
    {
            MusicBrainz5::CRecording *FullRelease=Metadata.Recording();

            FullRelease->Serialise(std::cout);
                if(artist.to8Bit() == FullRelease->Title())
        cout << "Music in Sync!";
    }

    cout << artist << endl;*/
    printf("Exited gracefully!");
    return 0;
}
