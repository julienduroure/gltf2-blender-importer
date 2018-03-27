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
from mathutils import Vector, Matrix, Quaternion
from ..buffer import *

class Skin():
    def __init__(self, index, json, gltf):
        self.index = index
        self.json  = json # skin json
        self.gltf  = gltf # Reference to global glTF instance
        self.name  = None
        self.bones = []
        self.blender_armature_name = None
        self.mesh_id = None

    def read(self):
        if 'skeleton' in self.json.keys():
            self.root = self.json['skeleton']

        if 'joints' in self.json.keys():
            self.bones = self.json['joints']

        if 'name' in self.json.keys():
            self.name = self.json['name']

        if 'inverseBindMatrices' in self.json.keys():
            self.inverseBindMatrices = Accessor(self.json['inverseBindMatrices'], self.gltf.json['accessors'][self.json['inverseBindMatrices']], self.gltf)
            self.data = self.inverseBindMatrices.read()
            self.inverseBindMatrices.debug_missing()

    def create_blender(self):
        if self.name is not None:
            name = self.name
        else:
            name = "Armature_" + str(self.index)

        armature = bpy.data.armatures.new(name)
        obj = bpy.data.objects.new(name, armature)
        bpy.data.scenes[self.gltf.blender.scene].objects.link(obj)
        self.blender_armature_name = obj.name


    def set_bone_transforms(self, bone, node, parent):
        obj   = bpy.data.objects[self.blender_armature_name]
        delta = Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0))

        mat = Matrix()
        if not parent:
            transform = node.get_transforms()
            mat = transform * delta.to_matrix().to_4x4()
        else:
            if not self.gltf.scene.nodes[parent].is_joint: # Node in another scene
                transform  = node.get_transforms()
                parent_mat = self.gltf.scene.nodes[parent].get_transforms()
            else:
                transform = node.get_transforms()
                parent_mat = obj.data.edit_bones[self.gltf.scene.nodes[parent].blender_bone_name].matrix # Node in another scene

            mat = (parent_mat.to_quaternion() * delta.inverted() * transform.to_quaternion() * delta).to_matrix().to_4x4()
            mat = Matrix.Translation(parent_mat.to_translation() + ( parent_mat.to_quaternion() * delta.inverted() * transform.to_translation() )) * mat


        bone.matrix = mat

    def create_bone(self, node, parent):
        scene = bpy.data.scenes[self.gltf.blender.scene]
        obj   = bpy.data.objects[self.blender_armature_name]

        bpy.context.screen.scene = scene
        scene.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")

        if node.name:
            name = node.name
        else:
            name = "Bone_" + str(node.index)

        bone = obj.data.edit_bones.new(name)
        node.blender_bone_name = bone.name
        bone.tail = Vector((0.0,1.0,0.0)) # Needed to keep bone alive
        self.set_bone_transforms(bone, node, parent)

        # Set parent
        if parent is not None and hasattr(self.gltf.scene.nodes[parent], "blender_bone_name"):
            bone.parent = obj.data.edit_bones[self.gltf.scene.nodes[parent].blender_bone_name] #TODO if in another scene

        bpy.ops.object.mode_set(mode="OBJECT")

    def create_vertex_groups(self):
        obj = bpy.data.objects[self.gltf.scene.nodes[self.mesh_id].blender_object]
        for bone in self.bones:
            obj.vertex_groups.new(self.gltf.scene.nodes[bone].blender_bone_name)

    def assign_vertex_groups(self):
        node = self.gltf.scene.nodes[self.mesh_id]
        obj = bpy.data.objects[node.blender_object]

        offset = 0
        for prim in node.mesh.primitives:
            if 'JOINTS_0' in prim.attributes.keys() and 'WEIGHTS_0' in prim.attributes.keys():

                joint_ = prim.attributes['JOINTS_0']['result']
                weight_ = prim.attributes['WEIGHTS_0']['result']

                for poly in obj.data.polygons:
                    for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                        vert_idx = obj.data.loops[loop_idx].vertex_index
                        if vert_idx in range(offset, offset + prim.vertices_length):

                            if offset != 0:
                                tab_index = vert_idx % offset
                            else:
                                tab_index = vert_idx

                            cpt = 0
                            for joint_idx in joint_[tab_index]:
                                weight_val = weight_[tab_index][cpt]

                                group = obj.vertex_groups[self.gltf.scene.nodes[self.bones[joint_idx]].blender_bone_name]
                                group.add([vert_idx], weight_val, 'REPLACE')
                                cpt += 1
            else:
                print("No Skinning ?????") #TODO


            offset = offset + prim.vertices_length

    def debug_missing(self):
        keys = [
                'skeleton',
                'joints',
                'name',
                'inverseBindMatrices'
                ]

        for key in self.json.keys():
            if key not in keys:
                print("SKIN MISSING " + key)
