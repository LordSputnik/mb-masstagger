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

import imp
import os

import plugins
import utils

def LoadPlugins():
    for directory, directories, filenames in os.walk( "./Warp/plugins" ):
        for filename in filenames:
            file_minus_ext, ext = os.path.splitext( filename )
            if ext == ".py":
                info = imp.find_module( file_minus_ext, ["./Warp/plugins"] )
                utils.safeprint( u"Found module {}".format( info ) )
                imp.load_module( "plugins." + file_minus_ext, *info )
