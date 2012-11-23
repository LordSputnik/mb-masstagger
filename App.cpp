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
#include "AudioFile.hpp"

namespace MassTagger
{
  namespace App
  {
    namespace
    {
      //'Private' variables
      boost::filesystem::path root_directory_("./");
      int result_;
      uint32_t num_mp3s = 0, num_flacs = 0, num_oggs = 0;
      std::list< std::shared_ptr<AudioFile> > music_files;
      std::map< std::string, std::shared_ptr<MusicBrainz5::CRelease> > release_map_;

      void ScanDirectory(const boost::filesystem::path & input_dir)
      {
        boost::filesystem::directory_iterator it(input_dir), end;
        for(;it != end; ++it)
        {
          if(is_directory(*it) == true)
          {
            ScanDirectory(*it);
            continue;
          }

          if(is_regular_file(*it) == false)
            continue;

          AudioFileType type = AudioFile::GetAudioFileType(*it);

          if(type == AUDIO_UNKNOWN)
            continue;

          if(type == AUDIO_FLAC)
            ++num_flacs;
          else if(type == AUDIO_MP3)
            ++num_mp3s;
          else if (type == AUDIO_VORBIS)
            ++num_oggs;

          std::shared_ptr<AudioFile> ptr(new AudioFile(*it,type));
          music_files.push_back(ptr);
        }
      }
    }

    //'Private' functions
    int Init(int argc, char* argv[])
    {
      for(int i = 1; i < argc; ++i)
      {
        puts(argv[i]);
        if(argv[i][0] != '-')
        {
          root_directory_ = argv[i];
        }
      }
      return result_;
    }

    void Run()
    {
      std::cout << "Boost Version: " << BOOST_LIB_VERSION << std::endl;
      if(exists(root_directory_))
      {
          ScanDirectory(root_directory_);
      }

      printf("Found %u MP3s, %u OGGs and %u FLACs.\n",num_mp3s,num_oggs,num_flacs);
    }

    int Destroy()
    {
      return result_;
    }

    MusicBrainz5::CRelease* LookupReleaseID(const std::string & uuid)
    {
      auto it = release_map_.find(uuid);

      if(it != release_map_.end())
        return it->second.get();

      MusicBrainz5::CQuery Query("masstagger-0.1");

      MusicBrainz5::CQuery::tParamMap Params;
      Params["inc"]="recordings";

      MusicBrainz5::CMetadata Metadata = Query.Query("release",uuid,"",Params);
      if (Metadata.Release())
      {
              MusicBrainz5::CRelease *FullRelease=Metadata.Release();

              std::cout << *FullRelease << std::endl;

              std::shared_ptr<MusicBrainz5::CRelease> ptr (Metadata.Release()->Clone()); // clone, so we get free of the auto deletion.
              release_map_[uuid] = ptr;
              return FullRelease;
      }
      return nullptr;

    }
  }
}
