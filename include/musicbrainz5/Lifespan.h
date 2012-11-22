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

#ifndef _MUSICBRAINZ5_LIFESPAN_H
#define _MUSICBRAINZ5_LIFESPAN_H

#include <string>
#include <iostream>

#include "musicbrainz5/Entity.h"

#include "musicbrainz5/xmlParser.h"

namespace MusicBrainz5
{
	class CLifespanPrivate;

	class CLifespan: public CEntity
	{
	public:
		CLifespan(const XMLNode& Node=XMLNode::emptyNode());
		CLifespan(const CLifespan& Other);
		CLifespan& operator =(const CLifespan& Other);
		virtual ~CLifespan();

		virtual CLifespan *Clone();

		std::string Begin() const;
		std::string End() const;
		std::string Ended() const;

		virtual std::ostream& Serialise(std::ostream& os) const;
		static std::string GetElementName();

	protected:
		virtual void ParseAttribute(const std::string& Name, const std::string& Value);
		virtual void ParseElement(const XMLNode& Node);

	private:
		CLifespanPrivate * const m_d;
	};
}

#endif
