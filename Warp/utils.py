# -*- coding: utf-8 -*-

# Copyright (C) 2012 Ben Ockmore

# This file is part of MusicBrainz MassTagger.

# MusicBrainz MassTagger is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# MusicBrainz MassTagger is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with MusicBrainz MassTagger. If not, see <http://www.gnu.org/licenses/>.

import re
import os
import sys
import unicodedata

#Note: A Lot of these functions were originally in MusicBrainz Picard. Used here under the terms on the GNU GPL 2+.
def sanitize_date(datestr):
    """Sanitize date format.

e.g.: "YYYY-00-00" -> "YYYY"
"YYYY- - " -> "YYYY"
...
"""
    date = []
    for num in datestr.split("-"):
        try:
            num = int(num.strip())
        except ValueError:
            break
        if num:
            date.append(num)
    return ("", "%04d", "%04d-%02d", "%04d-%02d-%02d")[len(date)] % tuple(date)

_re_slashes = re.compile(r'[\\/]', re.UNICODE)
def sanitize_filename(string, repl="_"):
    return _re_slashes.sub(repl, string)

def make_short_filename(prefix, filename, max_path_length=240, max_length=200,
                        mid_length=32, min_length=2):
    """
    Attempts to shorten the file name to the maximum allowed length.

    max_path_length: The maximum length of the complete path.
    max_length: The maximum length of a single file or directory name.
    mid_length: The medium preferred length of a single file or directory.
    min_length: The minimum allowed length of a single file or directory.
    """
    parts = [part.strip() for part in _re_slashes.split(filename)]
    parts.reverse()
    filename = os.path.join(*parts)
    left = len(prefix) + len(filename) + 1 - max_path_length

    for i in range(len(parts)):
        left -= max(0, len(parts[i]) - max_length)
        parts[i] = parts[i][:max_length]

    if left > 0:
        for i in range(len(parts)):
            length = len(parts[i]) - mid_length
            if length > 0:
                length = min(left, length)
                parts[i] = parts[i][:-length]
                left -= length
                if left <= 0:
                    break

        if left > 0:
            for i in range(len(parts)):
                length = len(parts[i]) - min_length
                if length > 0:
                    length = min(left, length)
                    parts[i] = parts[i][:-length]
                    left -= length
                    if left <= 0:
                        break

            if left > 0:
                raise IOError, "File name is too long."

    return os.path.join(*[a.strip() for a in reversed(parts)])

def pathcmp(a, b):
    return os.path.normcase(a) == os.path.normcase(b)

def asciipunct(s):
    mapping = {
        u"…": u"...",
        u"‘": u"'",
        u"’": u"'",
        u"‚": u"'",
        u"“": u"\"",
        u"”": u"\"",
        u"„": u"\"",
        u"′": u"'",
        u"″": u"\"",
        u"‹": u"<",
        u"›": u">",
        u"‐": u"-",
        u"‒": u"-",
        u"–": u"-",
        u"−": u"-",
        u"—": u"-",
        u"―": u"--",
    }
    for orig, repl in mapping.iteritems():
        s = s.replace(orig, repl)
    return s

_io_encoding = sys.getfilesystemencoding()
def encode_filename(filename):
    """Encode unicode strings to filesystem encoding."""
    if isinstance(filename, unicode):
        if os.path.supports_unicode_filenames and sys.platform != "darwin":
            return filename
        else:
            return filename.encode(_io_encoding, 'replace')
    else:
        return filename

def decode_filename(filename):
    """Decode strings from filesystem encoding to unicode."""
    if isinstance(filename, unicode):
        return filename
    else:
        return filename.decode(_io_encoding)

_re_win32_incompat = re.compile(r'["*:<>?|]', re.UNICODE)
def replace_win32_incompat(string, repl=u"_"):
    """Replace win32 filename incompatible characters from ``string`` by
       ``repl``."""
    return _re_win32_incompat.sub(repl, string)

_unaccent_dict = {u'Æ': u'AE', u'æ': u'ae', u'Œ': u'OE', u'œ': u'oe', u'ß': 'ss'}
_re_latin_letter = re.compile(r"^(LATIN [A-Z]+ LETTER [A-Z]+) WITH")
def unaccent(string):
    """Remove accents ``string``."""
    result = []
    for char in string:
        if char in _unaccent_dict:
            char = _unaccent_dict[char]
        else:
            try:
                name = unicodedata.name(char)
                match = _re_latin_letter.search(name)
                if match:
                    char = unicodedata.lookup(match.group(1))
            except:
                pass
        result.append(char)
    return "".join(result)

_re_non_ascii = re.compile(r'[^\x00-\x7F]', re.UNICODE)
def replace_non_ascii(string, repl="_"):
    """Replace non-ASCII characters from ``string`` by ``repl``."""
    return _re_non_ascii.sub(repl, asciipunct(string))