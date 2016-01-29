# Code404_Server - The serverside stuff and site for Code404_Server
# Copyright (C) 2015 Mitame, Doctor_N
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pygame import Surface, image, Rect, SRCALPHA
from os import remove

def surf_to_string(surface):
    image.save(surface, "/tmp/tempimage.png")
    string = open("/tmp/tempimage.png", "r").read()
    remove("/tmp/tempimage.png")
    return string


def get_and_crop(filepath, size):
    surf = get_image(filepath)
    return crop_center(surf, size)


def crop_center(image, size):
    rect = Rect((0, 0), size)
    res_surf = Surface(size, SRCALPHA, 32)
    blit_pos = [0, 0]
    if image.get_width() > rect.width:
        blit_pos[0] = (-image.get_width()+rect.width) // 2
    else:
        rect.x = (image.get_width()-rect.width) // 2
    if image.get_height() > rect.height:
        blit_pos[1] = (-image.get_height()+rect.height) // 2
    else:
        rect.y = (image.get_height()-rect.height) // 2

    print(rect)
    print(blit_pos)

    res_surf.blit(crop(image, rect), blit_pos)
    return res_surf


def crop(image, rect):
    res = Surface(rect.size, SRCALPHA, 32)
    res.blit(image, (0, 0), rect)
    return res


def get_image(filepath):
    return image.load(filepath)
