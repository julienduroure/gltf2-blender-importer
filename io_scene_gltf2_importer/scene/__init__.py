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

import bpy

from ..node import *

class Scene():
    def __init__(self, index, json, gltf):
        self.json = json   # Scene json
        self.gltf = gltf # Reference to global glTF instance
        self.nodes = {}

    def read(self):
        if 'name' in self.json.keys():
            self.name = self.json['name']
            print("Scene " + self.json['name'])
        else:
            self.name = None
            print("Scene...")


        for node_idx in self.json['nodes']:
            node = Node(node_idx, self.gltf.json['nodes'][node_idx], self.gltf, True, self)
            node.read()
            node.debug_missing()
            self.nodes[node_idx] = node

    def blender_create(self):
    # Create a new scene only if not already exists in .blend file
    # TODO : put in current scene instead ?
        if self.name not in [scene.name for scene in bpy.data.scenes]:
            if self.name:
                scene = bpy.data.scenes.new(self.name)
            else:
                scene = bpy.data.scenes.new('Scene')
            scene.render.engine = "CYCLES"

            self.gltf.blender.set_scene(scene.name)
        else:
            self.gltf.blender.set_scene(self.name)

        for node in self.nodes.values():
            if node.root:
                node.blender_create(None) # None => No parent


    # TODO create blender for other scenes

    def debug_missing(self):
        keys = [
                'nodes',
                'name'
                ]

        for key in self.json.keys():
            if key not in keys:
                print("SCENE MISSING " + key)
