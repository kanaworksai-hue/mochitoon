# SPDX-License-Identifier: GPL-3.0-or-later
"""One-call Python API, meant for AI agents and scripts.

    import bpy
    bpy.ops.mochitoon.make_cute(palette="SAKURA", shape="HEART", target="ALL", setup_scene=True)

or, from Python inside Blender:

    from <this package> import api
    api.make_cute(palette="pumpkin", shape="heart")
"""

import bpy

from . import core, nodes
from .palettes import ORDER, PALETTES, hex_to_linear

STYLE_IDS = {key: value for key, _, value in nodes.STYLES}
AMOUNTS = {"FEW": 0.15, "SOME": 0.3, "MANY": 0.55, "LOTS": 0.8}
MESHY = {"MESH", "CURVE", "SURFACE", "META", "FONT"}


def palette_key(name):
    key = (name or "SAKURA").strip().upper().replace(" ", "_").replace("-", "_")
    if key not in PALETTES:
        raise ValueError(f"Unknown palette {name!r}. Choose one of: {', '.join(ORDER)}")
    return key


def style_id(name):
    if name in (None, "", "KEEP"):
        return None
    key = str(name).strip().upper()
    if key not in STYLE_IDS:
        raise ValueError(f"Unknown dot style {name!r}. Choose one of: {', '.join(STYLE_IDS)}")
    return STYLE_IDS[key]


def amount_value(amount):
    if amount in (None, "", "KEEP"):
        return None
    if isinstance(amount, (int, float)):
        return float(amount)
    key = str(amount).strip().upper()
    if key not in AMOUNTS:
        raise ValueError(f"Unknown amount {amount!r}. Use {', '.join(AMOUNTS)} or a number 0-1")
    return AMOUNTS[key]


def resolve_objects(target="SELECTED", names=None, context=None):
    context = context or bpy.context
    scene = context.scene
    if names:
        objs = [scene.objects[n] for n in names if n in scene.objects]
    elif target == "ALL":
        objs = list(scene.objects)
    else:
        objs = list(context.selected_objects)
        if not objs and target == "SELECTED_OR_ALL":
            objs = list(scene.objects)
    return [o for o in objs if o.type in MESHY]


def make_cute(objects=None, palette="SAKURA", shape=None, keep_colors=None, outline=True,
              outline_width=0.02, setup_scene=False, target="SELECTED_OR_ALL", context=None,
              style=None, amount=None, light_rim=None, glow=None):
    """Apply MochiToon. Returns a short human-readable report.

    shape: one or more of CIRCLE HEART STAR FLOWER SPARKLE MOON ("STAR+FLOWER" or a list)
    style: GRID (classic halftone) or SPRINKLE (scattered stickers); amount: FEW/SOME/MANY/LOTS or 0-1
    light_rim / glow: 0-1"""
    context = context or bpy.context
    key = palette_key(palette)
    objs = objects if objects is not None else resolve_objects(target, context=context)
    if not objs:
        return "No mesh objects to change."
    core.parse_shapes(shape)  # validate before touching the scene
    sid = style_id(style)
    amt = amount_value(amount)
    if keep_colors is None:
        # textured models keep their texture by default; plain objects take the palette color
        keep_colors = any(core.base_color_texture(s.material) for o in objs for s in o.material_slots)
    if setup_scene:
        core.setup_scene(context.scene, key)
        if context.screen:
            core.setup_viewports(context.screen)
    n = core.apply_to_objects(objs, key, keep_colors=keep_colors)
    pal = PALETTES[key]
    line = core.outline_material(hex_to_linear(pal["line"]), pal["label"])
    for ob in objs:
        for slot in ob.material_slots:
            node = nodes.find_core_node(slot.material)
            if node is None:
                continue
            core.set_shapes(node, shape)
            if sid is not None:
                node.inputs["Dot Style"].default_value = sid
            if amt is not None:
                node.inputs["Sprinkle Amount"].default_value = amt
                if sid is None:
                    node.inputs["Dot Style"].default_value = 1  # asking for an amount means stickers
            if light_rim is not None:
                node.inputs["Light Rim Amount"].default_value = float(light_rim)
            if glow is not None:
                node.inputs["Glow"].default_value = float(glow)
        if outline:
            core.add_outline(ob, core.outline_thickness_for(ob, outline_width), line)
        else:
            core.remove_outline(ob)
    return f"MochiToon {pal['label']} applied to {n} object(s)."


def list_palettes():
    return [(k, PALETTES[k]["label"], PALETTES[k]["description"]) for k in ORDER]
