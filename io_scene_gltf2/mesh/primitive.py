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

from ..buffer import *
from ..material import *

class Primitive():
    def __init__(self, json, gltf):
        self.json  = json  # Primitive json
        self.gltf = gltf # Reference to global glTF instance
        self.attributes = {}
        self.mat = None
        self.targets = []

    def read(self):

        # reading attributes
        if 'attributes' in self.json.keys():
            for attr in self.json['attributes'].keys():
                print("Primitive attribute " + attr)
                self.attributes[attr] = {}
                self.attributes[attr]['accessor'] = Accessor(self.json['attributes'][attr], self.gltf.json['accessors'][self.json['attributes'][attr]], self.gltf)
                self.attributes[attr]['result']   = self.attributes[attr]['accessor'].read()
                self.attributes[attr]['accessor'].debug_missing()

        # reading indices
        if 'indices' in self.json.keys():
            print("Primitive indices")
            self.accessor = Accessor(self.json['indices'], self.gltf.json['accessors'][self.json['indices']], self.gltf)
            self.indices  = self.accessor.read()
            self.indices  = [ind[0] for ind in self.indices]
            self.accessor.debug_missing()
        else:
            self.indices = range(0, len(self.attributes['POSITION']['result']))


        # reading materials
        if 'material' in self.json.keys():
            # create material if not alreadt exits
            if self.json['material'] not in self.gltf.materials.keys():
                self.mat = Material(self.json['material'], self.gltf.json['materials'][self.json['material']], self.gltf)
                self.mat.read()
                self.mat.debug_missing()
                self.gltf.materials[self.json['material']] = self.mat
            else:
                # Use already existing material
                self.mat = self.gltf.materials[self.json['material']]

        # reading targets (shapekeys) if any
        if 'targets' in self.json.keys():
            for targ in self.json['targets']:
                target = {}
                for attr in targ.keys():
                    target[attr] = {}
                    target[attr]['accessor'] = Accessor(targ[attr], self.gltf.json['accessors'][targ[attr]], self.gltf)
                    target[attr]['result']   = target[attr]['accessor'].read()
                    target[attr]['accessor'].debug_missing()
                self.targets.append(target)

    def debug_missing(self):
        keys = [
                'indices',
                'attributes',
                'material',
                'targets'
                ]

        for key in self.json.keys():
            if key not in keys:
                print("PRIMITIVE MISSING " + key)
