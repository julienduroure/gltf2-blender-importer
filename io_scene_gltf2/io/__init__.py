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

import json

from ..scene import *
from ..animation import *



#TODO : to remove, is this class really needed?
class BlenderData():
    def __init__(self):
        pass

    def set_scene(self, scene_name):
        self.scene = scene_name


class glTFImporter():




    def __init__(self, filename):
        self.filename = filename
        self.other_scenes = []


        self.buffers = {}
        self.materials = {}

        self.load()

        self.blender = BlenderData()

        # TODO check version

        self.fmt_char_dict = {}
        self.fmt_char_dict[5120] = 'b' # Byte
        self.fmt_char_dict[5121] = 'B' # Unsigned Byte
        self.fmt_char_dict[5122] = 'h' # Short
        self.fmt_char_dict[5123] = 'H' # Unsigned Short
        self.fmt_char_dict[5125] = 'I' # Unsigned Int
        self.fmt_char_dict[5126] = 'f' # Float

        self.component_nb_dict = {}
        self.component_nb_dict['SCALAR'] = 1
        self.component_nb_dict['VEC2']   = 2
        self.component_nb_dict['VEC3']   = 3
        self.component_nb_dict['VEC4']   = 4
        self.component_nb_dict['MAT2']   = 4
        self.component_nb_dict['MAT3']   = 9
        self.component_nb_dict['MAT4']   = 16

    def load_glb(self):
        header = struct.unpack_from('<I4s', self.content)
        self.version = header[1]

        offset = 12 # header size = 12

        # TODO check json type for chunk 0, and BIN type for next ones

        # json
        type, str_json, offset = self.load_chunk(offset)
        self.json = json.loads(str_json.decode('utf-8'))

        # binary data
        chunk_cpt = 0
        while offset < len(self.content):
            type, data, offset = self.load_chunk(offset)

            self.buffers[chunk_cpt] = Buffer(chunk_cpt, self.json['buffers'][chunk_cpt], self)
            self.buffers[chunk_cpt].data = data #TODO .length
            chunk_cpt += 1

        self.content = None


    def load_chunk(self, offset):
        chunk_header = struct.unpack_from('<I4s', self.content, offset)
        data_length  = chunk_header[0]
        data_type    = chunk_header[1]
        data         = self.content[offset + 8 : offset + 8 + data_length]

        return data_type, data, offset + 8 + data_length

    def load(self):
        with open(self.filename, 'rb') as f:
            self.content = f.read()


        self.is_glb_format = self.content[:4] == b'glTF'

        if not self.is_glb_format:
            self.content = None
            with open(self.filename, 'r') as f:
                content = f.read()
                self.json = json.loads(content)

        else:
            # Parsing glb file
            self.load_glb()


    def get_root_scene(self):
        if 'scene' in self.json.keys():
            return self.json['scene'], self.json['scenes'][self.json['scene']]
        return 0, self.json['scenes'][0]


    def read(self):

        idx, scene = self.get_root_scene()
        self.scene = Scene(idx, scene, self)
        if not scene:
            print("Error reading root scene")

        self.scene.read()
        self.scene.debug_missing()

        # manage all scenes (except root scene that is already managed)
        scene_idx = 0
        for scene_it in self.json['scenes']:
            if scene_idx == idx:
                continue
            scene = Scene(scene_idx, self.json['scenes'][scene_idx] , self)
            scene.read()
            scene.debug_missing()
            scene_idx += 1
            self.other_scenes.append(scene)


        # manage animations
        if 'animations' in self.json.keys():
            anim_idx = 0
            for anim in self.json['animations']:
                animation = Animation(anim_idx, self.json['animations'][anim_idx], self)
                animation.read()

    def get_node(self, node_id):
        if node_id in self.scene.nodes.keys():
            return self.scene.nodes[node_id]
        for scene in self.other_scenes:
            if node_id in scene.nodes.keys():
                return scene.nodes[node_id]


    def blender_create(self):
        self.scene.blender_create()

        for scene in self.other_scenes:
            scene.blender_create()


    def debug_missing(self):
        keys = [
                'scene',
                'nodes',
                'scenes',
                'meshes',
                'accessors',
                'bufferViews',
                'buffers',
                'materials',
                'animations'
                ]

        for key in self.json.keys():
            if key not in keys:
                print("GLTF MISSING " + key)
