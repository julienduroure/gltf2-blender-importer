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

class Pbr():
    def __init__(self, json, gltf):
        self.json = json # pbrMetallicRoughness json
        self.gltf = gltf # Reference to global glTF instance

        # Default values
        self.baseColorFactor = [1,1,1,1]
        self.baseColorTexture = None
        self.metallicFactor = 1
        self.roughnessFactor = 1
        self.metallicRoughnessTexture = None
        self.extensions = None
        self.extras = None

    def read(self):
        if self.json is None:
            return # will use default values

        # TODO : no texture mode for now

        if 'baseColorFactor' in self.json.keys():
            self.baseColorFactor = self.json['baseColorFactor']

        if 'metallicFactor' in self.json.keys():
            self.metallicFactor = self.json['metallicFactor']

        if 'roughnessFactor' in self.json.keys():
            self.roughnessFactor = self.json['roughnessFactor']

    def create_blender(self, mat_name):
        engine = bpy.context.scene.render.engine
        if engine == 'CYCLES':
            self.create_blender_cycles(mat_name)
        else:
            pass #TODO for internal / Eevee in future 2.8

    def create_blender_cycles(self, mat_name):
        material = bpy.data.materials[mat_name]
        material.use_nodes = True
        node_tree = material.node_tree

        # delete all nodes except output
        for node in list(node_tree.nodes):
            if not node.type == 'OUTPUT_MATERIAL':
                node_tree.nodes.remove(node)

        output_node = node_tree.nodes[0]

        # create PBR node
        principled = node_tree.nodes.new('ShaderNodeBsdfPrincipled')

        # change input values
        principled.inputs[0].default_value = self.baseColorFactor
        principled.inputs[4].default_value = self.metallicFactor
        principled.inputs[5].default_value = self.metallicFactor #TODO : currently set metallic & specular in same way
        principled.inputs[7].default_value = self.roughnessFactor

        # link node to output
        node_tree.links.new(output_node.inputs[0], principled.outputs[0])

    def debug_missing(self):
        if self.json is None:
            return
        keys = [
                'baseColorFactor',
                'metallicFactor',
                'roughnessFactor'
                ]

        for key in self.json.keys():
            if key not in keys:
                print("PBR MISSING " + key)
