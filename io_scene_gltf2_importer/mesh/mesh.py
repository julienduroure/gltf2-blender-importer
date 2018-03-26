"""
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor(s): Julien Duroure.
 *
 * ***** END GPL LICENSE BLOCK *****
 """

from .primitive import *
from ..rig import *

class Mesh():
    def __init__(self, index, json, gltf):
        self.index = index
        self.json = json    # Mesh json
        self.gltf = gltf  # Reference to global glTF instance
        self.primitives = []
        self.target_weights = []
        self.name = None
        self.skin = None


    def read(self):
        if 'name' in self.json.keys():
            self.name = self.json['name']
            print("Mesh " + self.json['name'])
        else:
            print("Mesh index " + str(self.index))

        for primitive_it in self.json['primitives']:
            primitive = Primitive(primitive_it, self.gltf)
            primitive.read()
            self.primitives.append(primitive)
            primitive.debug_missing()

        # reading default targets weights if any
        if 'weights' in self.json.keys():
            for weight in self.json['weights']:
                self.target_weights.append(weight)

    def rig(self, skin_id):
        if skin_id not in self.gltf.skins.keys():
            self.skin = Skin(skin_id, self.gltf.json['skins'][skin_id], self.gltf)
            self.gltf.skins[skin_id] = self.skin
            self.skin.read()
            self.skin.debug_missing()
        else:
            self.skin = self.gltf.skins[skin_id]

    def debug_missing(self):
        keys = [
                'name',
                'primitives',
                'weights'
                ]

        for key in self.json.keys():
            if key not in keys:
                print("MESH MISSING " + key)
