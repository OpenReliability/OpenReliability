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

"""Module for defining the default colors proposed by the color
    picker tool.
    The position in the list define the position in the color
    picker window.
"""

from .. import qtall as qt4

listColor = (   qt4.QColor(213, 62, 79),        # RED
                qt4.QColor(50, 136, 189),       # BLUE
                qt4.QColor(102, 166, 30),       # GREEN
                qt4.QColor(244, 109, 67),       # ORANGE
                qt4.QColor(230, 171, 2),        # GOLD
                qt4.QColor(128, 115, 172),      # VIOLET

                qt4.QColor(166, 118, 29),       # BROWN
                qt4.QColor(102, 102, 102),      # GRAY
                qt4.QColor(188, 128, 189),      # PINK
                qt4.QColor(166, 206, 227),      # SOFT BLUE
                qt4.QColor(178, 223, 138),      # SOFT GREEN
                qt4.QColor(251, 154, 153),      # SOFT PINK

                qt4.QColor(153, 52, 4),        # ORANGE BROWN
                qt4.QColor(204, 76, 2),
                qt4.QColor(236, 112, 20),
                qt4.QColor(254, 153, 41),
                qt4.QColor(254, 196, 79),
                qt4.QColor(254, 227, 145),

                qt4.QColor(165, 15, 21),         # RED
                qt4.QColor(203, 24, 29),
                qt4.QColor(239, 59, 44),
                qt4.QColor(251, 106, 74),
                qt4.QColor(252, 146, 114),
                qt4.QColor(252, 187, 161),

                qt4.QColor(0, 109, 44),         # GREEN
                qt4.QColor(35, 139, 69),
                qt4.QColor(65, 174, 118),
                qt4.QColor(102, 194, 164),
                qt4.QColor(153, 216, 201),
                qt4.QColor(204, 236, 230),

                qt4.QColor(8, 81, 156),         # BLUE
                qt4.QColor(33, 113, 181),
                qt4.QColor(66, 146, 198),
                qt4.QColor(107, 174, 214),
                qt4.QColor(158, 202, 225),
                qt4.QColor(198, 219, 239),


                qt4.QColor(84, 39, 143),        # VIOLET
                qt4.QColor(106, 81, 163),
                qt4.QColor(128, 125, 186),
                qt4.QColor(158, 154, 200),
                qt4.QColor(188, 189, 220),
                qt4.QColor(218, 218, 235),

                qt4.QColor(37, 37, 37),         # GRAY
                qt4.QColor(82, 82, 82),
                qt4.QColor(115, 115, 115),
                qt4.QColor(150, 150, 150),
                qt4.QColor(189, 189, 189),
                qt4.QColor(217, 217, 217),
            )

for idx, color in enumerate(listColor):
    qt4.QColorDialog.setStandardColor(idx, color)
