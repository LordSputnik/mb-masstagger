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

#ifndef _MUSICBRAINZ5_ARTIST_CREDIT_H
#define _MUSICBRAINZ5_ARTIST_CREDIT_H

#include <iostream>

#include "musicbrainz5/Entity.h"
#include "musicbrainz5/NameCreditList.h"

#include "musicbrainz5/xmlParser.h"

namespace MusicBrainz5
{
	class CArtistCreditPrivate;

	class CArtistCredit: public CEntity
	{
	public:
		CArtistCredit(const XMLNode& Node=XMLNode::emptyNode());
		CArtistCredit(const CArtistCredit& Other);
		CArtistCredit& operator =(const CArtistCredit& Other);
		virtual ~CArtistCredit();

		virtual CArtistCredit *Clone();

		CNameCreditList *NameCreditList() const;

		virtual std::ostream& Serialise(std::ostream& os) const;
		static std::string GetElementName();

	protected:
		virtual void ParseAttribute(const std::string& Name, const std::string& Value);
		virtual void ParseElement(const XMLNode& Node);

	private:
		void Cleanup();

		CArtistCreditPrivate * const m_d;
	};
}

#endif
