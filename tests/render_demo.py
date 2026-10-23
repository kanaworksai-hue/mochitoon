"""Headless render test.

Run:
  "/Applications/Blender 5.2.app/Contents/MacOS/Blender" -b --factory-startup \
      --python tests/render_demo.py -- <output.png> [palette] [shape]
"""

import math
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import mochitoon  # noqa: E402
from mochitoon import core, nodes  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_path = argv[0] if argv else os.path.join(ROOT, "tests", "out", "demo.png")
palette = argv[1] if len(argv) > 1 else "SAKURA"
shape = int(argv[2]) if len(argv) > 2 else 0
# extra "Input Name=value" overrides, e.g. "Dot Density=140"
overrides = dict(a.split("=", 1) for a in argv[3:])

mochitoon.register()
scene = bpy.context.scene

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)


def add(op, **kw):
    op(**kw)
    ob = bpy.context.object
    return ob


def subsurf(ob, levels=2):
    m = ob.modifiers.new("Subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels


big = add(bpy.ops.mesh.primitive_uv_sphere_add, radius=1.0, location=(-2.0, 0, 0), segments=64, ring_count=32)
small = add(bpy.ops.mesh.primitive_uv_sphere_add, radius=0.7, location=(-0.1, 0.2, -0.3), segments=64, ring_count=32)
monkey = add(bpy.ops.mesh.primitive_monkey_add, size=1.4, location=(1.8, 0, -0.1), rotation=(0, 0, math.radians(-25)))
subsurf(monkey)

# a little cat head
head = add(bpy.ops.mesh.primitive_uv_sphere_add, radius=0.75, location=(0.1, -0.2, 1.65), segments=64, ring_count=32)
head.scale = (1.15, 0.95, 0.9)
ears = []
for side in (-1, 1):
    ear = add(bpy.ops.mesh.primitive_cone_add, radius1=0.32, depth=0.6, vertices=32,
              location=(0.1 + side * 0.5, -0.2, 2.25), rotation=(0, math.radians(side * 22), 0))
    ears.append(ear)
eyes = []
for side in (-1, 1):
    eye = add(bpy.ops.mesh.primitive_uv_sphere_add, radius=0.2, location=(0.1 + side * 0.32, -0.83, 1.7),
              segments=32, ring_count=16)
    eye.scale = (1, 0.5, 1.1)
    eyes.append(eye)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (0.2, -9.5, 1.6)
cam.rotation_euler = (math.radians(88), 0, 0)
cam_data.lens = 45
scene.camera = cam

core.setup_scene(scene, palette)
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.filepath = out_path
if hasattr(scene.eevee, "taa_render_samples"):
    scene.eevee.taa_render_samples = 16

core.apply_to_objects([big, small, monkey, head] + ears, palette)
core.apply_to_objects(eyes, "LEMON")
line = core.outline_material(core.hex_to_linear(core.PALETTES[palette]["line"]), palette)
for ob in [big, small, monkey, head] + ears + eyes:
    core.add_outline(ob, core.outline_thickness_for(ob, 0.02), line)

for mat in bpy.data.materials:
    node = nodes.find_core_node(mat)
    if node is not None:
        core.set_shapes(node, shape)
        for name, value in overrides.items():
            node.inputs[name].default_value = float(value)

bpy.ops.render.render(write_still=True)
print("RENDERED", out_path)
