# -*- coding: utf-8 -*-

# Copyright (C) 2013 Ben Ockmore

# This file is part of Warp Tagger.

# Warp Tagger is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# Warp Tagger is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Warp Tagger. If not, see <http://www.gnu.org/licenses/>.

MULTI_VALUED_JOINER = "; "

class Metadata( dict ):

    def copy( self, other ):
        self.clear()
        for key, values in other.rawitems():
            self.set( key, values[:] )

    def update( self, other ):
        for name, values in other.rawitems():
            self.set( name, values[:] )

    def getall( self, name ):
        return dict.get( self, name, [] )

    def get( self, name, default=None ):
        values = dict.get( self, name, None )
        if values:
            return MULTI_VALUED_JOINER.join( values )
        else:
            return default

    def __getitem__( self, name ):
        return self.get( name, u'' )

    def set( self, name, values ):
        dict.__setitem__( self, name, values )

    def __setitem__( self, name, values ):
        if not isinstance( values, list ):
            values = [values]
        values = filter( None, map( unicode, values ) )
        if len( values ):
            self.set( name, values )
        else:
            self.pop( name, None )

    def add( self, name, value ):
        if value or value == 0:
            self.setdefault( name, [] ).append( value )

    def add_unique( self, name, value ):
        if value not in self.getall( name ):
            self.add( name, value )

    def iteritems( self ):
        for name, values in dict.iteritems( self ):
            for value in values:
                yield name, value

    def items( self ):
        return list( self.iteritems() )

    def rawitems( self ):
        return dict.items( self )

    def apply_func( self, func ):
        for key, values in self.rawitems():
            if not key.startswith( "~" ):
                self[key] = map( func, values )

    def strip_whitespace( self ):
        self.apply_func( lambda s: s.strip() )
