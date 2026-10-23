"""Operator smoke test (headless).

Run:
  "/Applications/Blender 5.2.app/Contents/MacOS/Blender" -b --factory-startup --python tests/test_ops.py
"""

import os
import sys
import traceback

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import mochitoon  # noqa: E402
from mochitoon import core, nodes  # noqa: E402

failures = []


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        failures.append(label)


try:
    mochitoon.register()
    scene = bpy.context.scene
    s = scene.mochitoon

    # an object that already has a red material, to test "Keep Object Colors"
    bpy.ops.mesh.primitive_cube_add(location=(3, 0, 0))
    red_cube = bpy.context.object
    red = bpy.data.materials.new("Red")
    bsdf = next(n for n in red.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.8, 0.05, 0.05, 1.0)
    red_cube.data.materials.append(red)

    bpy.ops.mesh.primitive_uv_sphere_add()
    sphere = bpy.context.object

    for ob in scene.objects:
        ob.select_set(ob.type == "MESH")
    bpy.context.view_layer.objects.active = sphere

    s.palette = "MINT"
    bpy.ops.mochitoon.setup_scene()
    check("engine is EEVEE", scene.render.engine.startswith("BLENDER_EEVEE"))
    check("view transform Standard", scene.view_settings.view_transform == "Standard")

    s.keep_colors = True
    bpy.ops.mochitoon.apply()
    cube_mat = red_cube.material_slots[0].material
    check("cube got a MochiToon material", core.is_mochi(cube_mat))
    base = nodes.find_core_node(cube_mat).inputs["Base Color"].default_value
    check("keep colors kept red", abs(base[0] - 0.8) < 1e-3 and base[1] < 0.1)
    check("sphere got a MochiToon material", core.is_mochi(sphere.material_slots[0].material))
    check("outline modifier added", sphere.modifiers.get(core.OUTLINE_MOD) is not None)
    check("line slot is last", core.is_line(sphere.data.materials[-1]))
    mod = sphere.modifiers[core.OUTLINE_MOD]
    check("outline offset points at line slot", mod.material_offset == len(sphere.data.materials) - 1)

    # applying twice must not stack outlines or slots
    bpy.ops.mochitoon.apply()
    check("re-apply keeps one line slot", sum(core.is_line(m) for m in sphere.data.materials) == 1)
    check("re-apply keeps one outline modifier", sum(m.type == "SOLIDIFY" for m in sphere.modifiers) == 1)

    s.keep_colors = False
    s.palette = "SAKURA"
    bpy.ops.mochitoon.apply()
    mat = sphere.material_slots[0].material
    check("palette material named Sakura", "Sakura" in mat.name)

    s.palette = "NEON_NIGHT"
    bpy.ops.mochitoon.recolor()
    node = nodes.find_core_node(mat)
    check("recolor applied neon rim", node.inputs["Rim Amount"].default_value == 1.0)
    check("recolor swapped line material", "Neon" in sphere.data.materials[-1].name)

    bpy.ops.mochitoon.set_shape(shape="HEART", exclusive=True)
    check("shape set to heart only", core.enabled_shapes(node) == ["HEART"])
    bpy.ops.mochitoon.set_shape(shape="STAR")
    check("star added to the mix", core.enabled_shapes(node) == ["HEART", "STAR"])
    bpy.ops.mochitoon.set_style(style=1)
    check("sprinkle style", node.inputs["Dot Style"].default_value == 1)

    s.outline_width = 0.05
    check("outline width updates modifier", abs(mod.thickness - core.outline_thickness_for(sphere, 0.05)) < 1e-6)

    bpy.ops.mochitoon.outline_remove()
    check("outline removed", sphere.modifiers.get(core.OUTLINE_MOD) is None)
    check("line slot removed", not any(core.is_line(m) for m in sphere.data.materials))
    bpy.ops.mochitoon.outline_add()
    check("outline re-added", sphere.modifiers.get(core.OUTLINE_MOD) is not None)

    # one-call agent operator
    bpy.ops.mesh.primitive_cube_add(location=(-3, 0, 0))
    cube = bpy.context.object
    for ob in scene.objects:
        ob.select_set(False)
    r = bpy.ops.mochitoon.make_cute(palette="pumpkin", shape="SPARKLE", target="ALL", setup_scene=True)
    check("bloom compositor set", scene.compositing_node_group is not None)
    check("make_cute finished", r == {"FINISHED"})
    cn = nodes.find_core_node(cube.material_slots[0].material)
    check("make_cute hit unselected cube (target ALL)", cn is not None and cube.material_slots[0].material["mochitoon_palette"] == "PUMPKIN")
    check("make_cute set sparkle", core.enabled_shapes(cn) == ["SPARKLE"])
    bpy.ops.mochitoon.make_cute(palette="pumpkin", shape="star+flower+moon", amount="few", light_rim=0.8, glow=0.5,
                                target="ALL")
    cn = nodes.find_core_node(cube.material_slots[0].material)
    check("mixed shapes", core.enabled_shapes(cn) == ["STAR", "FLOWER", "MOON"])
    check("amount turns on sprinkle", cn.inputs["Dot Style"].default_value == 1 and
          abs(cn.inputs["Sprinkle Amount"].default_value - 0.15) < 1e-6)
    check("light rim + glow", cn.inputs["Light Rim Amount"].default_value > 0.7 and cn.inputs["Glow"].default_value > 0.4)
    check("cube keeps hard edges", any(e.use_edge_sharp for e in cube.data.edges) or not all(p.use_smooth for p in cube.data.polygons))
    try:
        bad = bpy.ops.mochitoon.make_cute(palette="rainbow")
    except RuntimeError as err:  # ERROR reports raise when called from Python
        bad = "raised" if "Unknown palette" in str(err) else str(err)
    check("unknown palette is rejected with the list", bad in ({"CANCELLED"}, "raised"))

    check("one core group", sum(g.name.startswith(nodes.GROUP_NAME) for g in bpy.data.node_groups) == 1)

    mochitoon.unregister()
    check("unregistered", not hasattr(bpy.types.Scene, "mochitoon"))
except Exception:
    traceback.print_exc()
    failures.append("exception")

print("RESULT", "OK" if not failures else f"FAILED {failures}")
