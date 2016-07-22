# -*- coding: utf-8 -*-
#    Copyright (C) 2016 Emmanuel Chery
#    Email: Emmanuel Chery <emmanuel.chery@ams.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
###############################################################################

"""Module for adding some fonts to the default system list.
    The fonts are located in the fonts fonts folder of OpenReliability
"""

import os
import inspect
from .. import qtall as qt4

# List all system fonts
db = qt4.QFontDatabase
# Find where we are
currentPath = inspect.getfile(inspect.currentframe())
# Go up 3 levels
for x in range(0, 3):
    currentPath = os.path.dirname(currentPath)
# Fonts folder
fontPath = os.path.join(currentPath,u'fonts')
# Add the fonts
for font in os.walk(fontPath):
    newFontPath = os.path.join(os.path.abspath(os.path.curdir), font[0])
    for file in os.listdir(newFontPath):
        if file.endswith(".ttf"):
            db.addApplicationFont(os.path.join(newFontPath, file))