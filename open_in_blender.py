"""Import the reference-based gateway into Blender and save a native .blend.

Run create_mihrab.py first, then in a terminal:
    blender --python open_in_blender.py
Or open this script in Blender's Text Editor and press Run Script.
No camera, lighting rig, or render is created.
"""
import bpy
import math
import mathutils
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OBJ=ROOT/"mihrab_qom.obj"
BLEND=ROOT/"mihrab_qom.blend"
if not OBJ.exists():
    raise FileNotFoundError("Run create_mihrab.py first; missing "+str(OBJ))

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.length_unit='METERS'

# Preserve the OBJ's native Z-up coordinates and all 5,000+ separate modules.
if hasattr(bpy.ops.wm,"obj_import"):
    bpy.ops.wm.obj_import(filepath=str(OBJ),forward_axis='NEGATIVE_Y',up_axis='Z')
else:
    bpy.ops.import_scene.obj(filepath=str(OBJ),use_split_objects=True,
                             use_split_groups=True,axis_forward='-Y',axis_up='Z')
imported=[obj for obj in scene.objects if obj.type=='MESH']

root=bpy.data.collections.new("GATEWAY | Persian tiled portal")
scene.collection.children.link(root)
groups={}
def group_for(name):
    if name.startswith(("FACADE_BRICK_","OUTER_SIDE_BRICK_","PASSAGE_CHEEK_BRICK_")):
        key="01 | Hand-laid sandstone brickwork"
    elif name.startswith(("ARCH_RING_","JAMB_RING_")):
        key="02 | Pointed arch + jamb archivolt"
    elif name.startswith(("FACADE_MOSAIC_","MOSAIC_")):
        key="03 | Glazed tympanum mosaic + rosettes"
    elif name.startswith("VAULT_SOFFIT_"):
        key="04 | Deep tiled vault soffit"
    elif name.startswith(("PLINTH_","BASE_","THRESHOLD_","CROWN_")):
        key="05 | Plinth, threshold + cornice"
    elif name.startswith("SHRINE_"):
        key="06 | Shrine facade + entrance"
    elif name.startswith(("DOME_","MINARET_")):
        key="07 | Dome + twin minarets"
    elif name.startswith("RIWAQ_"):
        key="08 | Flanking courtyard arcades"
    elif name.startswith(("COURTYARD_","LANTERN_")):
        key="09 | Paving, planting + lamps"
    else:
        key="10 | Structural cores + spandrels"
    if key not in groups:
        coll=bpy.data.collections.new(key)
        root.children.link(coll)
        groups[key]=coll
    return groups[key]
for obj in imported:
    dest=group_for(obj.name)
    for coll in list(obj.users_collection): coll.objects.unlink(obj)
    dest.objects.link(obj)
    obj.name=obj.name.replace('.','_')
    obj.data.name=obj.name+" | mesh"

colors={
    "Brick_Sandstone":(0.59,0.34,0.19),"Brick_Buff":(0.70,0.45,0.27),
    "Brick_Honey":(0.77,0.53,0.32),"Brick_Shadow":(0.43,0.25,0.15),
    "Mortar_Lime":(0.57,0.49,0.39),"Tile_Cobalt_Glaze":(0.025,0.075,0.32),
    "Tile_Deep_Blue_Glaze":(0.018,0.045,0.19),"Tile_Lapis_Glaze":(0.07,0.20,0.61),
    "Tile_Turquoise_Glaze":(0.015,0.39,0.43),"Tile_Teal_Glaze":(0.012,0.22,0.25),
    "Tile_Ivory_Glaze":(0.84,0.72,0.53),"Tile_Gold_Glaze":(0.78,0.43,0.10),
    "Foliage_Evergreen":(0.055,0.19,0.085),"Wood_Dark":(0.25,0.12,0.065),
    "Stone_Carved":(0.62,0.56,0.45),"Structure_Core":(0.48,0.39,0.29),
}
for name,rgb in colors.items():
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color=(*rgb,1.0)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value=(*rgb,1.0)
        is_glazed=name.startswith("Tile_")
        bsdf.inputs["Roughness"].default_value=0.19 if is_glazed else (0.82 if name.startswith("Brick_") else 0.70)
        if "Coat Weight" in bsdf.inputs: bsdf.inputs["Coat Weight"].default_value=0.32 if is_glazed else 0.0
        if "Coat Roughness" in bsdf.inputs: bsdf.inputs["Coat Roughness"].default_value=0.13
for obj in imported:
    for slot in obj.material_slots:
        if slot.material and slot.material.name in bpy.data.materials:
            slot.material=bpy.data.materials[slot.material.name]

# Open on a front elevation in material-colored solid shading; deliberately no render setup.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_location=(0.0,7.0,5.20)
            space.region_3d.view_distance=23.0
            space.region_3d.view_rotation=mathutils.Euler((math.radians(90),0,0),'XYZ').to_quaternion()
            space.region_3d.view_perspective='ORTHO'
            space.shading.type='SOLID'
            space.shading.color_type='MATERIAL'

bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print(f"Saved {BLEND} | {len(imported):,} independent mesh objects | texture-ready UVs")
