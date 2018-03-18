# glTF2 blender importer

This blender addon is in an early development stage.  
You will find some bugs, code may need some big refactoring.  
Feel free to contribute :)  
Current version may not fully follow glTF2 specification. This will change in near future ;-)

# Installation

Easier way to install this addon is to zip the io_scene_gltf2 directory, and to install this zip file as any other blender addons.

# What will NOT work (for now, until I implement it)  
*  materials (there are only created, but no data on it)
*  textures
*  rigging data (no joins, no skinning)

# What should work  
*  files  
    *  glb  
    *  gltf  
        *  with external uri  
        *  with embeded data  
*  geometry
*  children management
*  Morph (shapekeys)
*  animations  
    *  node animations  
    *  morph animations (shapekeys)  

# Thanks

Sources of inspiration / technical stuff:  
*  [Khronos glTF2 blender exporter](1)
*  [another gltf2 importer for blender][2]
*  [Overwiew of specification][3]
*  [glTF2 samples][4]

[1]: https://github.com/KhronosGroup/glTF-Blender-Exporter
[2]: https://github.com/ksons/gltf-blender-importer
[3]: https://github.com/KhronosGroup/glTF/blob/master/specification/2.0/figures/gltfOverview-2.0.0a.png
[4]: https://github.com/KhronosGroup/glTF-Sample-Models
