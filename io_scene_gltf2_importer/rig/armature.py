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
from mathutils import Vector
from ..buffer import *

class Skin():
    def __init__(self, index, json, gltf):
        self.index = index
        self.json  = json # skin json
        self.gltf  = gltf # Reference to global glTF instance
        self.name  = None
        self.bones = []
        self.blender_armature_name = None

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
        # Need to set head & tail locations to keep this bone alive
        bone.head = Vector((0.0,0.0,0.0)) # TODO get transformations
        bone.tail = Vector((0.0,0.0,1.0)) # TODO get transformations

        # Set parent
        if parent is not None and hasattr(self.gltf.scene.nodes[parent], "blender_bone_name"):
            bone.parent = obj.data.edit_bones[self.gltf.scene.nodes[parent].blender_bone_name] #TODO if in another scene

        bpy.ops.object.mode_set(mode="OBJECT")

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
