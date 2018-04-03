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
    def __init__(self, index, json, gltf):
        self.index = index
        self.json  = json  # Primitive json
        self.gltf = gltf # Reference to global glTF instance
        self.attributes = {}
        self.mat = None
        self.targets = [] # shapekeys
        self.blender_texcoord = {}

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
            # create material if not already exits
            if self.json['material'] not in self.gltf.materials.keys():
                self.mat = Material(self.json['material'], self.gltf.json['materials'][self.json['material']], self.gltf)
                self.mat.read()
                self.mat.debug_missing()
                self.gltf.materials[self.json['material']] = self.mat

                if 'COLOR_0' in self.attributes.keys():
                    self.mat.use_vertex_color()

            else:
                # Use already existing material
                self.mat = self.gltf.materials[self.json['material']]

        else:
            # If there is a COLOR_0, we are going to use it in material
            if 'COLOR_0' in self.attributes.keys():
                self.mat = Material(None, None, self.gltf)
                self.mat.read()
                self.mat.debug_missing()
                self.mat.use_vertex_color()
            else:
                # No material, use default one
                if self.gltf.default_material is None:
                    self.gltf.default_material = Material(None, None, self.gltf)
                    self.gltf.default_material.read()
                    self.gltf.default_material.debug_missing()

                self.mat = self.gltf.default_material

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


    def blender_create(self, verts, edges, faces):
        # TODO mode of primitive 4 for now.
        current_length = len(verts)
        prim_verts = [self.gltf.convert.location(vert) for vert in self.attributes['POSITION']['result']]
        self.vertices_length = len(prim_verts)
        verts.extend(prim_verts)
        prim_faces = []
        for i in range(0, len(self.indices), 3):
            vals = self.indices[i:i+3]
            new_vals = []
            for y in vals:
                new_vals.append(y+current_length)
            prim_faces.append(tuple(new_vals))
        faces.extend(prim_faces)
        self.faces_length = len(prim_faces)

        # manage material of primitive
        if self.mat:

            # Create Blender material
            if not self.mat.blender_material:
                self.mat.create_blender()

        return verts, edges, faces

    def debug_missing(self):
        keys = [
                'indices',
                'attributes',
                'material',
                'targets'
                ]

        keys_attr = [
                'POSITION',
                'NORMAL',
                'TEXCOORD_0',
                'TEXCOORD_1',
                'JOINTS_0',
                'WEIGHTS_0'
        ]

        for key in self.json.keys():
            if key not in keys:
                print("PRIMITIVE MISSING " + key)

        if 'attributes' in self.json.keys():
            for attr in self.json['attributes'].keys():
                if attr not in keys_attr:
                    print("PRIMITIVE MISSING attribute " + attr)
