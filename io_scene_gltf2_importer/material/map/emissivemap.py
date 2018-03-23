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

from .map import *

class EmissiveMap(Map):
    def __init__(self, json, factor, gltf):
        super(EmissiveMap, self).__init__(json, factor, gltf)

    def create_blender(self, mat_name):
        engine = bpy.context.scene.render.engine
        if engine == 'CYCLES':
            self.create_blender_cycles(mat_name)
        else:
            pass #TODO for internal / Eevee in future 2.8

    def create_blender_cycles(self, mat_name):
        material = bpy.data.materials[mat_name]
        node_tree = material.node_tree

        self.texture.blender_create()

        # retrieve principled node and output node
        principled = [node for node in node_tree.nodes if node.type == "BSDF_PRINCIPLED"][0]
        output = [node for node in node_tree.nodes if node.type == 'OUTPUT_MATERIAL'][0]

        # add nodes
        emit = node_tree.nodes.new('ShaderNodeEmission')
        separate = node_tree.nodes.new('ShaderNodeSeparateRGB')
        combine = node_tree.nodes.new('ShaderNodeCombineRGB')
        mapping = node_tree.nodes.new('ShaderNodeMapping')
        uvmap = node_tree.nodes.new('ShaderNodeUVMap')
        text  = node_tree.nodes.new('ShaderNodeTexImage')
        text.image = bpy.data.images[self.texture.image.blender_image_name]
        add = node_tree.nodes.new('ShaderNodeAddShader')

        math_R  = node_tree.nodes.new('ShaderNodeMath')
        math_R.operation = 'MULTIPLY'
        math_R.inputs[1].default_value = self.factor[0]

        math_G  = node_tree.nodes.new('ShaderNodeMath')
        math_G.operation = 'MULTIPLY'
        math_G.inputs[1].default_value = self.factor[1]

        math_B  = node_tree.nodes.new('ShaderNodeMath')
        math_B.operation = 'MULTIPLY'
        math_B.inputs[1].default_value = self.factor[2]

        # create links
        node_tree.links.new(mapping.inputs[0], uvmap.outputs[0])
        node_tree.links.new(text.inputs[0], mapping.outputs[0])
        node_tree.links.new(separate.inputs[0], text.outputs[0])
        node_tree.links.new(math_R.inputs[0], separate.outputs[0])
        node_tree.links.new(math_G.inputs[0], separate.outputs[1])
        node_tree.links.new(math_B.inputs[0], separate.outputs[2])
        node_tree.links.new(combine.inputs[0], math_R.outputs[0])
        node_tree.links.new(combine.inputs[1], math_G.outputs[0])
        node_tree.links.new(combine.inputs[2], math_B.outputs[0])
        node_tree.links.new(emit.inputs[0], combine.outputs[0])

        # following  links will modify PBR node tree
        node_tree.links.new(add.inputs[0], emit.outputs[0])
        node_tree.links.new(add.inputs[1], principled.outputs[0])
        node_tree.links.new(output.inputs[0], add.outputs[0])
