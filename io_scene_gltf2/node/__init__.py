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
import bmesh

from mathutils import Matrix, Vector, Quaternion

from ..mesh import *
from ..camera import *

class Node():
    def __init__(self, index, json, gltf, root, scene):
        self.index = index
        self.json = json   # Node json
        self.gltf = gltf # Reference to global glTF instance
        self.root = root
        self.scene = scene # Reference to scene
        self.mesh = None
        self.children = []
        self.blender_object = ""
        self.anims = []

    def read(self):
        if 'name' in self.json.keys():
            self.name = self.json['name']
            print("Node " + self.json['name'])
        else:
            self.name = None
            print("Node index " + str(self.index))

        self.transform = self.get_transforms()

        if 'mesh' in self.json.keys():
            self.mesh = Mesh(self.json['mesh'], self.gltf.json['meshes'][self.json['mesh']], self.gltf)
            self.mesh.read()
            self.mesh.debug_missing()


        if not 'children' in self.json.keys():
            return

        for child in self.json['children']:
            child = Node(child, self.gltf.json['nodes'][child], self.gltf, False, self.scene)
            child.read()
            child.debug_missing()
            self.children.append(child)
            self.scene.nodes[child.index] = child

    def set_anim(self, channel):
        self.anims.append(channel)

    def convert_matrix(self, mat):
        mat =  Matrix([mat[0:4], mat[4:8], mat[8:12], mat[12:16]])
        mat.transpose()
        return mat

    def convert_quaternion(self, q):
        return Quaternion([q[3], q[0], -q[2], q[1]])

    def convert_location(self, location):
        return [location[0], -location[2], location[1]]

    def convert_scale(self, scale):
        return scale # TODO test scale animation

    def get_transforms(self):

        if 'matrix' in self.json.keys():
            return self.convert_matrix(self.json['matrix'])

        mat = Matrix()


        if 'scale' in self.json.keys():
            s = self.json['scale']
            mat = Matrix([
                [s[0], 0, 0, 0],
                [0, s[1], 0, 0],
                [0, 0, s[2], 0],
                [0, 0, 0, 1]
            ])


        if 'rotation' in self.json.keys():
            q = self.convert_quaternion(self.json['rotation'])
            mat = q.to_matrix().to_4x4() * mat

        if 'translation' in self.json.keys():
            mat = Matrix.Translation(Vector(self.convert_location(self.json['translation']))) * mat

        return mat


    def set_transforms(self, obj):
        obj.matrix_world =  self.transform


    def set_parent(self, obj, parent):

        if parent is None:
            return

        for node in self.gltf.scene.nodes.values(): # TODO if parent is in another scene
            if node.index == parent:
                if node.blender_object:
                    obj.parent = bpy.data.objects[node.blender_object]
                    return

        print("ERROR, parent not found")

    def blender_create_anim(self):
        obj = bpy.data.objects[self.blender_object]
        fps = bpy.context.scene.render.fps
        first_anim = True
        for anim in self.anims:
            if anim.path in ['translation', 'rotation', 'scale']:

                if anim.path == "translation":
                    blender_path = "location"
                    for key in anim.data:
                       obj.location = Vector(self.convert_location(list(key[1])))
                       obj.keyframe_insert(blender_path, frame = key[0] * fps, group='location')

                    # Setting interpolation
                    for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                        for kf in fcurve.keyframe_points:
                            self.set_interpolation(anim.interpolation, kf)

                elif anim.path == "rotation":
                    blender_path = "rotation_quaternion"
                    for key in anim.data:
                        obj.rotation_quaternion = self.convert_quaternion(key[1])
                        obj.keyframe_insert(blender_path, frame = key[0] * fps, group='rotation')

                    # Setting interpolation
                    for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                        for kf in fcurve.keyframe_points:
                            self.set_interpolation(anim.interpolation, kf)


                elif anim.path == "scale":
                    blender_path = "scale"
                    for key in anim.data:
                        obj.scale = Vector(self.convert_scale(list(key[1])))
                        obj.keyframe_insert(blender_path, frame = key[0] * fps, group='scale')

                    # Setting interpolation
                    for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                        for kf in fcurve.keyframe_points:
                            self.set_interpolation(anim.interpolation, kf)

            elif anim.path == 'weights':
                cpt_sk = 0
                for sk in anim.data:
                    for key in sk:
                        obj.data.shape_keys.key_blocks[cpt_sk+1].value = key[1]
                        obj.data.shape_keys.key_blocks[cpt_sk+1].keyframe_insert("value", frame=key[0] * fps, group='ShapeKeys')

                    cpt_sk += 1

            if first_anim == True:
                first_anim = False
                if anim.anim.name and obj.animation_data and obj.animation_data.action:
                    obj.animation_data.action.name = anim.anim.name

    def set_interpolation(self, interpolation, kf):
        if interpolation == "LINEAR":
            kf.interpolation = 'LINEAR'
        elif interpolation == "STEP":
            kf.interpolation = 'CONSTANT'
        elif interpolation == "CATMULLROMSPLINE":
            kf.interpolation = 'BEZIER' #TODO
        elif interpolation == "CUBICSPLINE":
            kf.interpolation = 'BEZIER' #TODO
        else:
            print("Unknown interpolation : " + self.interpolation)
            kf.interpolation = 'BEZIER'

    def blender_create(self, parent):
        if self.mesh:
            if self.mesh.name:
                mesh_name = self.mesh.name
            else:
                if self.name:
                    mesh_name = self.name
                else:
                    mesh_name = "Mesh_" + str(self.index)

            if self.name:
                name = self.name
            else:
                name = "Object_" + str(self.index)

            mesh = bpy.data.meshes.new(mesh_name)
            # TODO mode of primitive 4 for now.
            # TODO move some parts on mesh / primitive classes ?
            verts = []
            edges = []
            faces = []
            for prim in self.mesh.primitives:
                current_length = len(verts)
                verts.extend([self.convert_location(vert) for vert in prim.attributes['POSITION']['result']])
                prim_faces = []
                for i in range(0, len(prim.indices), 3):
                    vals = prim.indices[i:i+3]
                    new_vals = []
                    for y in vals:
                        new_vals.append(y+current_length)
                    prim_faces.append(tuple(new_vals))
                faces.extend(prim_faces)
                prim.faces_length = len(prim_faces)

                # manage material of primitive
                if prim.mat:
                    if not prim.mat.index in self.gltf.materials.keys():
                        print("Error, material should exist")

                    # Create Blender material
                    if not prim.mat.blender_material:
                        prim.mat.create_blender()

            mesh.from_pydata(verts, edges, faces)
            mesh.validate()

            cpt_vert = 0
            for prim in self.mesh.primitives:
                if 'NORMAL' in prim.attributes.keys():
                    for vert in mesh.vertices:
                        vert.normal = prim.attributes['NORMAL']['result'][cpt_vert]
                cpt_vert += 1


            mesh.update()
            obj = bpy.data.objects.new(name, mesh)
            obj.rotation_mode = 'QUATERNION'
            bpy.data.scenes[self.gltf.blender.scene].objects.link(obj)
            self.set_transforms(obj)
            self.blender_object = obj.name
            self.set_parent(obj, parent)


            # Assign materials to mesh
            offset = 0
            cpt_index = 0
            for prim in self.mesh.primitives:
                if not prim.mat:
                    continue
                obj.data.materials.append(bpy.data.materials[prim.mat.blender_material])
                for loop in range(offset, offset + prim.faces_length):
                    obj.data.polygons[loop].material_index = cpt_index
                offset = offset + prim.faces_length
                cpt_index += 1

            # Create shapekeys if needed
            max_shape_to_create = 0
            for prim in self.mesh.primitives:
                if len(prim.targets) > max_shape_to_create:
                    max_shape_to_create = len(prim.targets)

            # Create basis shape key
            if max_shape_to_create > 0:
                obj.shape_key_add("Basis")

            for i in range(max_shape_to_create):

                obj.shape_key_add("target_" + str(i)) #TODO name (can be in json file)

                for prim in self.mesh.primitives:
                    if i > len(prim.targets):
                        continue

                    bm = bmesh.new()
                    bm.from_mesh(mesh)

                    shape_layer = bm.verts.layers.shape[i+1]
                    vert_idx = 0
                    for vert in bm.verts:
                        shape = vert[shape_layer]
                        co = self.convert_location(list(prim.targets[i]['POSITION']['result'][vert_idx]))
                        shape.x = obj.data.vertices[vert_idx].co.x + co[0]
                        shape.y = obj.data.vertices[vert_idx].co.y + co[1]
                        shape.z = obj.data.vertices[vert_idx].co.z + co[2]

                        vert_idx += 1

                    bm.to_mesh(obj.data)
                    bm.free()

            # set default weights for shape keys, and names
            for i in range(max_shape_to_create):
                if i < len(self.mesh.target_weights):
                    obj.data.shape_keys.key_blocks[i+1].value = self.mesh.target_weights[i]
                    if self.mesh.primitives[0].targets[i]['POSITION']['accessor'].name:
                       obj.data.shape_keys.key_blocks[i+1].name  = self.mesh.primitives[0].targets[i]['POSITION']['accessor'].name


            for child in self.children:
                child.blender_create(self.index)

            self.blender_create_anim()
            return

        # No mesh. For now, create empty #TODO

        if self.name:
            print("Blender create node " + self.name)
            obj = bpy.data.objects.new(self.name, None)
        else:
            obj = bpy.data.objects.new("Node", None)
        bpy.data.scenes[self.gltf.blender.scene].objects.link(obj)
        self.set_transforms(obj)
        self.blender_object = obj.name
        self.set_parent(obj, parent)
        self.blender_create_anim()

        for child in self.children:
            child.blender_create(self.index)

    def debug_missing(self):
        keys = [
                'name',
                'mesh',
                'matrix',
                'translation',
                'rotation',
                'scale',
                'children'
                ]

        for key in self.json.keys():
            if key not in keys:
                print("NODE MISSING " + key)
