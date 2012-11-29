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

#ifndef _MBMT_PCH_H_
#define _MBMT_PCH_H_

//STD C++
#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <list>
#include <memory>
#include <ctime>

//Boost C++
#include <boost/version.hpp>
#include <boost/filesystem.hpp>

//TagLib Includes
#include <taglib/taglib.h>
#include <taglib/fileref.h>
#include <taglib/tpropertymap.h>
#include <taglib/id3v2tag.h>
#include <taglib/id3v2header.h>


// MusicBrainz Includes
#include <musicbrainz5/Query.h>
#include <musicbrainz5/Disc.h>
#include <musicbrainz5/Release.h>
#include <musicbrainz5/ReleaseGroup.h>
#include <musicbrainz5/Recording.h>
#include <musicbrainz5/Track.h>
#include <musicbrainz5/MediumList.h>
#include <musicbrainz5/Medium.h>

#endif // _MBMT_PCH_H_
