"""Run inside Blender to import the generated model and save a native .blend.

Usage (Blender 3.6+):
    blender --python open_in_blender.py
or open the script in Blender's Text Editor and press Run Script.
The adjacent mihrab_qom.obj and mihrab_qom.mtl must be present.
"""
import bpy
from pathlib import Path
import math
import mathutils

ROOT = Path(__file__).resolve().parent
OBJ = ROOT / "mihrab_qom.obj"
BLEND = ROOT / "mihrab_qom.blend"
if not OBJ.exists():
    raise FileNotFoundError(f"{OBJ} not found; run create_mihrab.py first")

# Keep Blender's startup objects out of the architectural model.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    if collection.name != "Collection" and collection.users == 0:
        bpy.data.collections.remove(collection)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'

# Import all OBJ groups as independent Blender objects, preserving UVs and MTL.
if hasattr(bpy.ops.wm, "obj_import"):
    bpy.ops.wm.obj_import(filepath=str(OBJ), forward_axis='NEGATIVE_Y', up_axis='Z')
else:
    bpy.ops.import_scene.obj(filepath=str(OBJ), use_split_objects=True, use_split_groups=True,
                             axis_forward='-Y', axis_up='Z')
imported = [o for o in scene.objects if o.type == 'MESH']

# Organize for immediate, uncluttered work in the Outliner.
root_collection = bpy.data.collections.get("MIHRAB | Qom")
if root_collection is None:
    root_collection = bpy.data.collections.new("MIHRAB | Qom")
    scene.collection.children.link(root_collection)
subcollections = {}
def collection_for(name):
    if name.startswith("BRICK_"): key = "01 | Hand-laid clay bricks"
    elif name.startswith("ARCH_") or name.startswith("JAMB_"): key = "02 | Glazed arch voussoirs"
    elif name.startswith("NICHE_"): key = "03 | Recessed niche + mosaic"
    elif name.startswith("REVEAL_"): key = "04 | Niche inner reveals"
    elif name.startswith("SPANDREL_"): key = "05 | Spandrel tile medallions"
    elif name.startswith("WALL_"): key = "06 | Limestone backup"
    else: key = "07 | Plinth + crown"
    if key not in subcollections:
        coll = bpy.data.collections.new(key)
        root_collection.children.link(coll)
        subcollections[key] = coll
    return subcollections[key]
for obj in imported:
    # Remove imported objects from the scene's default collection(s), then link
    # them into their architectural group while keeping mesh data/UV maps.
    target = collection_for(obj.name)
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    target.objects.link(obj)
    obj.name = obj.name.replace('.', '_')
    obj.data.name = obj.name + " | mesh"
    obj.color = (0.62, 0.34, 0.20, 1.0) if obj.name.startswith("BRICK_") else (0.04,0.25,0.58,1.0)
    obj.display_type = 'TEXTURED'

# Set authored PBR materials: the glazed ceramics have a polished, glassy coat;
# the clay and limestone remain dry and matte. UV maps are preserved on every
# independent brick/tile, ready for an image texture to be added per part.
mat_rgb = {
    "Brick_Red_Clay": (0.48,0.19,0.105), "Brick_Warm_Clay": (0.61,0.29,0.16),
    "Brick_Light_Clay": (0.70,0.39,0.23), "Mortar_Stone": (0.66,0.62,0.53),
    "Tile_Cobalt_Glaze": (0.035,0.105,0.43), "Tile_Turquoise_Glaze": (0.02,0.48,0.52),
    "Tile_Lapis_Glaze": (0.08,0.24,0.70), "Tile_Ivory_Glaze": (0.88,0.78,0.59),
    "Tile_Teal_Glaze": (0.015,0.30,0.30), "Niche_Deep_Blue": (0.018,0.065,0.20),
    "Backing_Limestone": (0.59,0.54,0.44),
}
for name, color in mat_rgb.items():
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color,1.0)
        glazed = name.startswith("Tile_") or name == "Niche_Deep_Blue"
        bsdf.inputs["Roughness"].default_value = 0.19 if glazed else (0.82 if "Brick_" in name else 0.72)
        if "Metallic" in bsdf.inputs: bsdf.inputs["Metallic"].default_value = 0.0
        if "Coat Weight" in bsdf.inputs: bsdf.inputs["Coat Weight"].default_value = 0.30 if glazed else 0.0
        if "Coat Roughness" in bsdf.inputs: bsdf.inputs["Coat Roughness"].default_value = 0.14

for obj in imported:
    for slot in obj.material_slots:
        if slot.material:
            mat = bpy.data.materials.get(slot.material.name)
            if mat:
                slot.material = mat

# Readable, model-first opening view. No camera or render setup is created.
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type == 'VIEW_3D':
        space = area.spaces.active
        space.region_3d.view_location = (0.0, 0.0, 3.2)
        space.region_3d.view_distance = 9.6
        space.region_3d.view_rotation = mathutils.Euler((math.radians(90),0,0), 'XYZ').to_quaternion()
        space.region_3d.view_perspective = 'ORTHO'
        space.shading.type = 'MATERIAL'

# Save with all objects deselected; select the overall collection's contents only
# when the artist chooses them. Scene intentionally has no camera/lights/render.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
print(f"Saved {BLEND} with {len(imported)} separate mesh objects and per-object UVs")
