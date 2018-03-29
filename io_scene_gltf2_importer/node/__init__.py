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
        self.camera = None
        self.children = []
        self.blender_object = ""
        self.anims = {}
        self.is_joint = False
        self.parent = None

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

            if 'skin' in self.json.keys():
                self.mesh.rig(self.json['skin'], self.index)

        if 'camera' in self.json.keys():
            self.camera = Camera(self.json['camera'], self.name, self.gltf.json['cameras'][self.json['camera']], self.gltf)
            self.camera.read()
            self.camera.debug_missing()


        if not 'children' in self.json.keys():
            return

        for child in self.json['children']:
            child = Node(child, self.gltf.json['nodes'][child], self.gltf, False, self.scene)
            child.read()
            child.debug_missing()
            self.children.append(child)
            self.scene.nodes[child.index] = child

    def set_anim(self, channel):
        if channel.anim.index not in self.anims.keys():
            self.anims[channel.anim.index] = []
        self.anims[channel.anim.index].append(channel)

    def convert_matrix(self, mat_input):
        mat_input =  Matrix([mat_input[0:4], mat_input[4:8], mat_input[8:12], mat_input[12:16]])
        mat_input.transpose()

        s = mat_input.to_scale()
        rotation = mat_input.to_quaternion()
        location = mat_input.to_translation()

        mat = Matrix([
            [s[0], 0, 0, 0],
            [0, s[1], 0, 0],
            [0, 0, s[2], 0],
            [0, 0, 0, 1]
        ])

        mat = self.convert_matrix_quaternion(rotation).to_matrix().to_4x4() * mat
        mat = Matrix.Translation(Vector(self.convert_location(location))) * mat

        return mat

    def convert_quaternion(self, q):
        return Quaternion([q[3], q[0], -q[2], q[1]])

    def convert_matrix_quaternion(self, q):
        return Quaternion([q[0], q[1], -q[3], q[2]])

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

    def blender_bone_create_anim(self):
        obj   = bpy.data.objects[self.gltf.skins[self.skin_id].blender_armature_name]
        bone  = obj.pose.bones[self.blender_bone_name]
        fps = bpy.context.scene.render.fps
        delta = Quaternion((0.7071068286895752, 0.7071068286895752, 0.0, 0.0))

        for anim in self.anims.keys():
            if not self.gltf.animations[anim].blender_action:
                if self.gltf.animations[anim].name:
                    name = self.gltf.animations[anim].name
                else:
                    name = "Animation_" + str(self.gltf.animations[anim].index)
                action = bpy.data.actions.new(name)
                self.gltf.animations[anim].blender_action = action.name
            if not obj.animation_data:
                obj.animation_data_create()
            obj.animation_data.action = bpy.data.actions[self.gltf.animations[anim].blender_action]

            for channel in self.anims[anim]:
                if channel.path == "translation":
                    blender_path = "location"
                    for key in channel.data:
                        transform = Matrix.Translation(self.convert_location(list(key[1])))
                        if not self.parent:
                            mat = transform
                        else:
                            if not self.gltf.scene.nodes[self.parent].is_joint:
                                parent_mat = self.gltf.scene.nodes[self.parent].get_transforms()
                            else:
                                parent_mat = obj.pose.bones[self.gltf.scene.nodes[self.parent].blender_bone_name].matrix # Node in another scene

                            mat = (parent_mat.to_quaternion() * delta.inverted() * transform.to_quaternion() * delta).to_matrix().to_4x4()
                            mat = Matrix.Translation(parent_mat.to_translation() + ( parent_mat.to_quaternion() * delta.inverted() * transform.to_translation() )) * mat

                        mat = obj.convert_space(bone, mat, 'WORLD', 'LOCAL')
                        bone.location = mat.to_translation()
                        bone.keyframe_insert(blender_path, frame = key[0] * fps, group='location')


                    # Setting interpolation
                    for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                        for kf in fcurve.keyframe_points:
                            self.set_interpolation(channel.interpolation, kf)

                elif channel.path == "rotation":
                    blender_path = "rotation_quaternion"
                    for key in channel.data:
                        transform = (self.convert_quaternion(key[1])).to_matrix().to_4x4()
                        if not self.parent:
                            mat = transform
                        else:
                            if not self.gltf.scene.nodes[self.parent].is_joint:
                                parent_mat = self.gltf.scene.nodes[self.parent].get_transforms()
                            else:
                                parent_mat = obj.pose.bones[self.gltf.scene.nodes[self.parent].blender_bone_name].matrix # Node in another scene

                            mat = (parent_mat.to_quaternion() * delta.inverted() * transform.to_quaternion() * delta).to_matrix().to_4x4()
                            mat = Matrix.Translation(parent_mat.to_translation() + ( parent_mat.to_quaternion() * delta.inverted() * transform.to_translation() )) * mat

                        mat = obj.convert_space(bone, mat, 'WORLD', 'LOCAL')
                        bone.rotation_quaternion = mat.to_quaternion()
                        bone.keyframe_insert(blender_path, frame = key[0] * fps, group='rotation')

                    # Setting interpolation
                    for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                        for kf in fcurve.keyframe_points:
                            self.set_interpolation(channel.interpolation, kf)


                elif channel.path == "scale":
                    blender_path = "scale"
                    for key in channel.data:
                        s = self.convert_scale(list(key[1]))
                        transform = Matrix([
                            [s[0], 0, 0, 0],
                            [0, s[1], 0, 0],
                            [0, 0, s[2], 0],
                            [0, 0, 0, 1]
                        ])

                        if not self.parent:
                            mat = transform
                        else:
                            if not self.gltf.scene.nodes[self.parent].is_joint:
                                parent_mat = self.gltf.scene.nodes[self.parent].get_transforms()
                            else:
                                parent_mat = obj.pose.bones[self.gltf.scene.nodes[self.parent].blender_bone_name].matrix # Node in another scene

                            mat = (parent_mat.to_quaternion() * delta.inverted() * transform.to_quaternion() * delta).to_matrix().to_4x4()
                            mat = Matrix.Translation(parent_mat.to_translation() + ( parent_mat.to_quaternion() * delta.inverted() * transform.to_translation() )) * mat

                        mat = obj.convert_space(bone, mat, 'WORLD', 'LOCAL')
                        bone.scale = mat.to_scale()
                        bone.keyframe_insert(blender_path, frame = key[0] * fps, group='scale')

                    # Setting interpolation
                    for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                        for kf in fcurve.keyframe_points:
                            self.set_interpolation(channel.interpolation, kf)

    def blender_create_anim(self):
        obj = bpy.data.objects[self.blender_object]
        fps = bpy.context.scene.render.fps

        for anim in self.anims.keys():
            if not self.gltf.animations[anim].blender_action:
                if self.gltf.animations[anim].name:
                    name = self.gltf.animations[anim].name
                else:
                    name = "Animation_" + str(self.gltf.animations[anim].index)
                action = bpy.data.actions.new(name)
                self.gltf.animations[anim].blender_action = action.name
            if not obj.animation_data:
                obj.animation_data_create()
            obj.animation_data.action = bpy.data.actions[self.gltf.animations[anim].blender_action]

            for channel in self.anims[anim]:
                if channel.path in ['translation', 'rotation', 'scale']:

                    if channel.path == "translation":
                        blender_path = "location"
                        for key in channel.data:
                           obj.location = Vector(self.convert_location(list(key[1])))
                           obj.keyframe_insert(blender_path, frame = key[0] * fps, group='location')

                        # Setting interpolation
                        for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                            for kf in fcurve.keyframe_points:
                                self.set_interpolation(channel.interpolation, kf)

                    elif channel.path == "rotation":
                        blender_path = "rotation_quaternion"
                        for key in channel.data:
                            obj.rotation_quaternion = self.convert_quaternion(key[1])
                            obj.keyframe_insert(blender_path, frame = key[0] * fps, group='rotation')

                        # Setting interpolation
                        for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                            for kf in fcurve.keyframe_points:
                                self.set_interpolation(channel.interpolation, kf)


                    elif channel.path == "scale":
                        blender_path = "scale"
                        for key in channel.data:
                            obj.scale = Vector(self.convert_scale(list(key[1])))
                            obj.keyframe_insert(blender_path, frame = key[0] * fps, group='scale')

                        # Setting interpolation
                        for fcurve in [curve for curve in obj.animation_data.action.fcurves if curve.group.name == "rotation"]:
                            for kf in fcurve.keyframe_points:
                                self.set_interpolation(channel.interpolation, kf)

                elif channel.path == 'weights':
                    cpt_sk = 0
                    for sk in channel.data:
                        for key in sk:
                            obj.data.shape_keys.key_blocks[cpt_sk+1].value = key[1]
                            obj.data.shape_keys.key_blocks[cpt_sk+1].keyframe_insert("value", frame=key[0] * fps, group='ShapeKeys')

                        cpt_sk += 1

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
        self.parent = parent
        if self.mesh:

            # Check if the mesh is rigged, and create armature if needed
            if self.mesh.skin:
                if self.mesh.skin.blender_armature_name is None:
                    # Create empty armature for now
                    self.mesh.skin.create_blender_armature()

            if self.name:
                name = self.name
            else:
                # Take mesh name if exist
                if self.mesh.name:
                    name = self.mesh.name
                else:
                    name = "Object_" + str(self.index)

            # Geometry
            if self.mesh.name:
                mesh_name = self.mesh.name
            else:
                mesh_name = "Mesh_" + str(self.index)

            mesh = bpy.data.meshes.new(mesh_name)
            # TODO mode of primitive 4 for now.
            # TODO move some parts on mesh / primitive classes ?
            verts = []
            edges = []
            faces = []
            for prim in self.mesh.primitives:
                current_length = len(verts)
                prim_verts = [self.convert_location(vert) for vert in prim.attributes['POSITION']['result']]
                prim.vertices_length = len(prim_verts)
                verts.extend(prim_verts)
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

                    # Create Blender material
                    if not prim.mat.blender_material:
                        prim.mat.create_blender()

            mesh.from_pydata(verts, edges, faces)
            mesh.validate()


            # Normals
            offset = 0
            for prim in self.mesh.primitives:
                for poly in mesh.polygons:
                    for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                        vert_idx = mesh.loops[loop_idx].vertex_index
                        if vert_idx in range(offset, offset + prim.vertices_length):
                            if offset != 0:
                                cpt_vert = vert_idx % offset
                            else:
                                cpt_vert = vert_idx
                            mesh.vertices[vert_idx].normal = prim.attributes['NORMAL']['result'][cpt_vert]
            offset = offset + prim.vertices_length

            mesh.update()
            obj = bpy.data.objects.new(name, mesh)
            obj.rotation_mode = 'QUATERNION'
            bpy.data.scenes[self.gltf.blender.scene].objects.link(obj)
            self.set_transforms(obj)
            self.blender_object = obj.name
            self.set_parent(obj, parent)

            # manage UV
            offset = 0
            for prim in self.mesh.primitives:
                for texcoord in [attr for attr in prim.attributes.keys() if attr[:9] == "TEXCOORD_"]:
                    if not texcoord in mesh.uv_textures:
                        mesh.uv_textures.new(texcoord)
                        prim.blender_texcoord[int(texcoord[9:])] = texcoord

                    for poly in mesh.polygons:
                        for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                            vert_idx = mesh.loops[loop_idx].vertex_index
                            if vert_idx in range(offset, offset + prim.vertices_length):
                                obj.data.uv_layers[texcoord].data[loop_idx].uv = Vector((prim.attributes[texcoord]['result'][vert_idx-offset][0], 1-prim.attributes[texcoord]['result'][vert_idx-offset][1]))

                offset = offset + prim.vertices_length

            mesh.update()

            # Object and UV are now created, we can set UVMap into material
            for prim in self.mesh.primitives:
                if prim.mat.pbr.color_type in [prim.mat.pbr.TEXTURE, prim.mat.pbr.TEXTURE_FACTOR] :
                    prim.mat.set_uvmap(prim, obj)

            # Assign materials to mesh
            offset = 0
            cpt_index_mat = 0
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.faces.ensure_lookup_table()
            for prim in self.mesh.primitives:
                obj.data.materials.append(bpy.data.materials[prim.mat.blender_material])
                for vert in bm.verts:
                    if vert.index in range(offset, offset + prim.vertices_length):
                        for loop in vert.link_loops:
                            face = loop.face.index
                            bm.faces[face].material_index = cpt_index_mat
                cpt_index_mat += 1
                offset = offset + prim.vertices_length
            bm.to_mesh(obj.data)
            bm.free()

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


            # Apply vertex color.
            vertex_color = None
            offset = 0
            for prim in self.mesh.primitives:
                if 'COLOR_0' in prim.attributes.keys():
                    # Create vertex color, once only per object
                    if vertex_color is None:
                        vertex_color = obj.data.vertex_colors.new("COLOR_0")

                    color_data = prim.attributes['COLOR_0']['result']

                    for poly in mesh.polygons:
                        for loop_idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
                            vert_idx = mesh.loops[loop_idx].vertex_index
                            if vert_idx in range(offset, offset + prim.vertices_length):
                                if offset != 0:
                                    cpt_idx = vert_idx % offset
                                else:
                                    cpt_idx = vert_idx
                                vertex_color.data[loop_idx].color = color_data[cpt_idx][0:3]
                                #TODO : no alpha in vertex color
                offset = offset + prim.vertices_length

            for child in self.children:
                child.blender_create(self.index)

            self.blender_create_anim()
            return

        if self.camera:
            obj = self.camera.create_blender()
            self.set_transforms(obj) #TODO default rotation of cameras ?
            self.blender_object = obj.name
            self.set_parent(obj, parent)

            return


        if self.is_joint:
            # Check if corresponding armature is already created, create it if needed
            if self.gltf.skins[self.skin_id].blender_armature_name is None:
                self.gltf.skins[self.skin_id].create_blender_armature()

            self.gltf.skins[self.skin_id].create_bone(self, parent)

            self.blender_bone_create_anim()

            for child in self.children:
                child.blender_create(self.index)

            return

        # No mesh, no camera. For now, create empty #TODO

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
                'children',
                'camera',
                'skin'
                ]

        for key in self.json.keys():
            if key not in keys:
                print("NODE MISSING " + key)
