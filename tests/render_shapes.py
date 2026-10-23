# SPDX-FileCopyrightText: 2026 東京AI映像合同会社 (Tokyo AI Visuals LLC)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Shape sheet: one sphere per shape (sprinkle mode) + a mixed one, light rim and glow on.

  Blender -b --factory-startup --python tests/render_shapes.py -- out.png [GRID|SPRINKLE]
"""

import math
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mochitoon import core, nodes  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
style = 1 if (len(argv) < 2 or argv[1].upper() == "SPRINKLE") else 0
scene = bpy.context.scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scene.collection.objects.link(cam)
cam.location = (0, -12.5, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
cam.data.lens = 50
scene.camera = cam
core.setup_scene(scene, "PUMPKIN")
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
scene.eevee.taa_render_samples = 16

sets = [["CIRCLE"], ["HEART"], ["STAR"], ["FLOWER"], ["SPARKLE"], ["MOON"], ["HEART", "STAR", "FLOWER"],
        ["STAR", "MOON", "SPARKLE"]]
keys = ["SAKURA", "PEACH", "LEMON", "MINT", "SODA", "GRAPE", "SAKURA", "WITCH"]
for i, (shapes, key) in enumerate(zip(sets, keys)):
    x = (i % 4 - 1.5) * 2.4
    z = 1.2 - (i // 4) * 2.4
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(x, 0, z), segments=64, ring_count=32)
    ob = bpy.context.object
    core.apply_to_objects([ob], key)
    ob.material_slots[0].material = ob.material_slots[0].material.copy()
    node = nodes.find_core_node(ob.material_slots[0].material)
    core.set_shapes(node, shapes)
    node.inputs["Dot Style"].default_value = style
    node.inputs["Highlight Size"].default_value = 0.6
    node.inputs["Dot Density"].default_value = 30.0 if style else 60.0
    node.inputs["Sprinkle Amount"].default_value = 0.4
    node.inputs["Spin"].default_value = 0.15
    node.inputs["Light Rim Amount"].default_value = 1.0
    node.inputs["Glow"].default_value = 0.6
    node.inputs["Rim Amount"].default_value = 0.6
    pal = core.PALETTES[key]
    core.add_outline(ob, 0.03, core.outline_material(core.hex_to_linear(pal["line"]), pal["label"]))

scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("RENDERED", out)
