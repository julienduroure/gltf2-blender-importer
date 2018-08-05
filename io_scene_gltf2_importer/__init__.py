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
 * This development is done in strong collaboration with Airbus Defence & Space
 """

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

from .io import *
from .scene import *
from .util import *

bl_info = {
    "name": "glTF2 importer",
    "version": (0, 0, 4),
    "author": "Julien Duroure",
    "blender": (2, 79, 0),
    "description": "glTF2 importer",
    "location": "File > Import",
    "category": "Import-Export"
}

#TODO reloading stuff

class ImportglTF2(Operator, ImportHelper):
    bl_idname = 'import_scene.gltf2'
    bl_label  = "Import glTF2"

    loglevel = bpy.props.EnumProperty(items=Log.getLevels(), description="Log Level", default=Log.default())

    def execute(self, context):
        return self.import_gltf2(context)

    def import_gltf2(self, context):
        bpy.context.scene.render.engine = 'CYCLES'
        self.gltf = glTFImporter(self.filepath, self.loglevel)
        self.gltf.log.critical("Starting loading glTF file")
        success, txt = self.gltf.read()
        if not success:
            self.report({'ERROR'}, txt)
            return {'CANCELLED'}
        self.gltf.log.critical("Data are loaded, start creating Blender stuff")
        self.gltf.blender_create()
        self.gltf.debug_missing()
        self.gltf.log.critical("glTF import is now finished")
        self.gltf.log.removeHandler(self.gltf.log_handler)

        # Switch to newly created main scene
        bpy.context.screen.scene = bpy.data.scenes[self.gltf.blender.scene]

        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportglTF2.bl_idname, text=ImportglTF2.bl_label)

def register():
    bpy.utils.register_class(ImportglTF2)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportglTF2)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
