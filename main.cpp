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

#include "pch.hpp"
#include "App.hpp"

using namespace std;

int main(int argc, char* argv[])
{
  if(MassTagger::App::Init(argc,argv) != 0)
  {
    return MassTagger::App::Destroy();
  }

  MassTagger::App::Run();

  return MassTagger::App::Destroy();
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


    /*
     // artist == "Frank Zappa"


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
}
