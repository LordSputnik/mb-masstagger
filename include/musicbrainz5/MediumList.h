/* --------------------------------------------------------------------------

   libmusicbrainz5 - Client library to access MusicBrainz

   Copyright (C) 2012 Andrew Hawkins

   This file is part of libmusicbrainz5.

   This library is free software; you can redistribute it and/or
   modify it under the terms of v2 of the GNU Lesser General Public
   License as published by the Free Software Foundation.

   libmusicbrainz5 is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this library.  If not, see <http://www.gnu.org/licenses/>.

     $Id$

----------------------------------------------------------------------------*/

#ifndef _MUSICBRAINZ5_MEDIUM_LIST_H
#define _MUSICBRAINZ5_MEDIUM_LIST_H

#include <string>
#include <iostream>

#include "musicbrainz5/ListImpl.h"

#include "musicbrainz5/xmlParser.h"

namespace MusicBrainz5
{
	class CMedium;
	class CMediumListPrivate;

	class CMediumList: public CListImpl<CMedium>
	{
	public:
		CMediumList(const XMLNode& Node=XMLNode::emptyNode());
		CMediumList(const CMediumList& Other);
		CMediumList& operator =(const CMediumList& Other);
		virtual ~CMediumList();

		virtual CMediumList *Clone();

		int TrackCount() const;

		virtual std::ostream& Serialise(std::ostream& os) const;
		static std::string GetElementName();

	protected:
		virtual void ParseAttribute(const std::string& Name, const std::string& Value);
		virtual void ParseElement(const XMLNode& Node);

	private:
		CMediumListPrivate * const m_d;
	};
}

#endif
