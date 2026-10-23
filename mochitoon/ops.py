# SPDX-FileCopyrightText: 2026 東京AI映像合同会社 (Tokyo AI Visuals LLC)
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty

from . import core, nodes, palettes
from .palettes import PALETTES, hex_to_linear

_previews = None
_enum_items = []


def _icon_pixels(pal, size=128):
    """Little preview: a shaded ball with a dotted highlight and an outline."""
    base = palettes.hex_to_srgb(pal["base"])
    tint = palettes.hex_to_srgb(pal["tint"])
    shadow = tuple(b * t for b, t in zip(base, tint))
    hi = palettes.hex_to_srgb(pal["highlight"])
    line = palettes.hex_to_srgb(pal["line"])
    bg = palettes.hex_to_srgb(pal["bg"])
    px = []
    c = (size - 1) / 2.0
    radius = size * 0.40
    for y in range(size):  # rows go bottom to top
        for x in range(size):
            dx, dy = (x - c) / radius, (y - c) / radius
            d = (dx * dx + dy * dy) ** 0.5
            if d > 1.12:
                col = bg
            elif d > 1.0:
                col = line
            else:
                nz = max(0.0, 1.0 - d * d) ** 0.5
                light = -0.55 * dx + 0.6 * dy + 0.58 * nz
                col = base if light > 0.25 else shadow
                hx, hy = dx + 0.35, dy - 0.35
                spot = 1.0 - (hx * hx + hy * hy) ** 0.5 / 0.45
                if spot > 0:
                    cell = size / 13.0
                    gx = (x % cell) - cell / 2
                    gy = (y % cell) - cell / 2
                    if (gx * gx + gy * gy) ** 0.5 < cell * 0.46 * spot ** 0.5:
                        col = hi
            px.extend((col[0], col[1], col[2], 1.0))
    return px


def _palette_items(self, context):
    return _enum_items


def _build_items():
    global _previews
    import bpy.utils.previews
    _previews = bpy.utils.previews.new()
    _enum_items.clear()
    for i, key in enumerate(palettes.ORDER):
        pal = PALETTES[key]
        icon = 0
        try:
            prev = _previews.new(key)
            prev.icon_size = (32, 32)
            prev.image_size = (128, 128)  # crisp in the big template_icon_view
            prev.image_pixels_float = _icon_pixels(pal)
            icon = prev.icon_id
        except Exception:
            pass
        _enum_items.append((key, pal["label"], pal["description"], icon, i))


def _outline_width_changed(self, context):
    for ob in context.selected_objects:
        mod = ob.modifiers.get(core.OUTLINE_MOD)
        if mod is not None:
            mod.thickness = core.outline_thickness_for(ob, self.outline_width)


class MochiToonSettings(bpy.types.PropertyGroup):
    palette: EnumProperty(name="Palette", items=_palette_items)
    keep_colors: BoolProperty(
        name="Keep Object Colors",
        description="Use each object's current color as the base and only take shadows and dots from the palette",
        default=False,
    )
    with_outline: BoolProperty(name="Outline", description="Add a comic outline when applying", default=True)
    outline_width: FloatProperty(
        name="Outline Width", description="Outline width relative to the object size",
        default=0.02, min=0.0, soft_max=0.1, precision=3, step=0.1, update=_outline_width_changed,
    )


def _selected_meshes(context):
    return [o for o in context.selected_objects if o.type in {"MESH", "CURVE", "SURFACE", "META", "FONT"}]


def _line_material(key):
    pal = PALETTES[key]
    return core.outline_material(hex_to_linear(pal["line"]), pal["label"])


def _mochi_materials(objects):
    seen = []
    for ob in objects:
        for slot in ob.material_slots:
            if core.is_mochi(slot.material) and slot.material not in seen:
                seen.append(slot.material)
    return seen


class MOCHITOON_OT_apply(bpy.types.Operator):
    bl_idname = "mochitoon.apply"
    bl_label = "Make It Cute"
    bl_description = "Give the selected objects the MochiToon comic look with the chosen palette"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(_selected_meshes(context))

    def execute(self, context):
        s = context.scene.mochitoon
        objs = _selected_meshes(context)
        n = core.apply_to_objects(objs, s.palette, keep_colors=s.keep_colors)
        if s.with_outline:
            line = _line_material(s.palette)
            for ob in objs:
                core.add_outline(ob, core.outline_thickness_for(ob, s.outline_width), line)
        if context.scene.render.engine not in {"BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"}:
            self.report({"WARNING"}, "MochiToon needs EEVEE. Click 'Setup Cute Scene' or switch the render engine")
        else:
            self.report({"INFO"}, f"MochiToon applied to {n} object(s)")
        return {"FINISHED"}


class MOCHITOON_OT_make_cute(bpy.types.Operator):
    """Everything in one call, for AI agents and scripts:
    bpy.ops.mochitoon.make_cute(palette="SAKURA", shape="HEART", target="ALL", setup_scene=True)"""
    bl_idname = "mochitoon.make_cute"
    bl_label = "Make Cute (one call)"
    bl_options = {"REGISTER", "UNDO"}

    palette: bpy.props.StringProperty(name="Palette", default="",
                                      description="Palette name, e.g. SAKURA, LEMON, NEON_NIGHT, PUMPKIN "
                                                  "(empty keeps the objects' palette, SAKURA for new ones)")
    shape: bpy.props.StringProperty(name="Shapes", default="",
                                    description="One or more of CIRCLE HEART STAR FLOWER SPARKLE MOON, e.g. STAR+FLOWER "
                                                "(empty keeps the current shapes)")
    style: bpy.props.StringProperty(name="Dot Style", default="",
                                    description="GRID (classic halftone) or SPRINKLE (scattered stickers)")
    amount: bpy.props.StringProperty(name="Amount", default="",
                                     description="Sticker amount: FEW, SOME, MANY, LOTS or a number 0-1")
    light_rim: bpy.props.FloatProperty(name="Light Rim", default=-1.0, min=-1.0, max=1.0,
                                       description="White rim on the lit side, 0-1 (-1 keeps it)")
    glow: bpy.props.FloatProperty(name="Glow", default=-1.0, min=-1.0, max=1.0,
                                  description="Bloom on the rim and dots, 0-1 (-1 keeps it)")
    target: EnumProperty(name="Target", default="SELECTED_OR_ALL", items=(
        ("SELECTED_OR_ALL", "Selected, else All", "Selected objects, or every mesh if nothing is selected"),
        ("SELECTED", "Selected", ""),
        ("ALL", "All", "Every mesh in the scene"),
    ))
    keep_colors: EnumProperty(name="Keep Colors", default="AUTO", items=(
        ("AUTO", "Auto", "Keep textures, recolor plain objects"),
        ("YES", "Yes", ""),
        ("NO", "No", ""),
    ))
    outline: BoolProperty(name="Outline", default=True)
    setup_scene: BoolProperty(name="Setup Cute Scene", default=False)
    smooth: BoolProperty(name="Smooth Low-Poly", default=False,
                         description="Add a Subdivision Surface modifier to low-poly, rounded meshes (skips boxy ones)")

    def execute(self, context):
        from . import api
        try:
            report = api.make_cute(
                palette=self.palette or None, shape=self.shape or None, target=self.target,
                style=self.style or None, amount=self.amount or None,
                light_rim=None if self.light_rim < 0 else self.light_rim, glow=None if self.glow < 0 else self.glow,
                smooth=self.smooth,
                keep_colors={"AUTO": None, "YES": True, "NO": False}[self.keep_colors],
                outline=self.outline, setup_scene=self.setup_scene, context=context,
            )
        except ValueError as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}
        self.report({"INFO"}, report)
        return {"FINISHED"}


class MOCHITOON_OT_recolor(bpy.types.Operator):
    bl_idname = "mochitoon.recolor"
    bl_label = "Recolor"
    bl_description = "Apply the chosen palette to the MochiToon materials of the selected objects"
    bl_options = {"REGISTER", "UNDO"}

    keep_base: BoolProperty(name="Keep Base Color", default=False)

    def execute(self, context):
        s = context.scene.mochitoon
        objs = _selected_meshes(context) or ([context.object] if context.object else [])
        mats = _mochi_materials(objs)
        for mat in mats:
            core.apply_palette(nodes.find_core_node(mat), s.palette, keep_base=self.keep_base)
        line = _line_material(s.palette)
        for ob in objs:
            if ob.modifiers.get(core.OUTLINE_MOD):
                core.add_outline(ob, ob.modifiers[core.OUTLINE_MOD].thickness, line)
        self.report({"INFO"}, f"Recolored {len(mats)} material(s)")
        return {"FINISHED"}


class MOCHITOON_OT_setup_scene(bpy.types.Operator):
    bl_idname = "mochitoon.setup_scene"
    bl_label = "Setup Cute Scene"
    bl_description = "EEVEE, exact (Standard) colors, a crisp sun and a flat background in the palette color"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        core.setup_scene(context.scene, context.scene.mochitoon.palette)
        if context.screen:
            core.setup_viewports(context.screen)
        return {"FINISHED"}


class MOCHITOON_OT_set_shape(bpy.types.Operator):
    bl_idname = "mochitoon.set_shape"
    bl_label = "Toggle Shape"
    bl_description = "Turn this shape on or off (shapes mix: each cell picks one of the enabled shapes)"
    bl_options = {"REGISTER", "UNDO"}

    shape: bpy.props.StringProperty(default="CIRCLE")
    exclusive: BoolProperty(default=False, description="Use only this shape")

    def execute(self, context):
        mat = context.object.active_material if context.object else None
        node = nodes.find_core_node(mat)
        if node is None:
            return {"CANCELLED"}
        on = set(core.enabled_shapes(node))
        key = self.shape.upper()
        if self.exclusive:
            on = {key}
        elif key in on and len(on) > 1:
            on.discard(key)
        else:
            on.add(key)
        core.set_shapes(node, on)
        return {"FINISHED"}


class MOCHITOON_OT_set_style(bpy.types.Operator):
    bl_idname = "mochitoon.set_style"
    bl_label = "Dot Style"
    bl_description = "Classic halftone grid, or scattered stickers"
    bl_options = {"REGISTER", "UNDO"}

    style: IntProperty(default=0, min=0, max=1)

    def execute(self, context):
        node = nodes.find_core_node(context.object.active_material if context.object else None)
        if node is None:
            return {"CANCELLED"}
        node.inputs["Dot Style"].default_value = self.style
        return {"FINISHED"}


class MOCHITOON_OT_outline_add(bpy.types.Operator):
    bl_idname = "mochitoon.outline_add"
    bl_label = "Add Outline"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        s = context.scene.mochitoon
        line = _line_material(s.palette)
        for ob in _selected_meshes(context):
            current = next((m for m in ob.data.materials if core.is_line(m)), None) if ob.type == "MESH" else None
            core.add_outline(ob, core.outline_thickness_for(ob, s.outline_width), current or line)
        return {"FINISHED"}


class MOCHITOON_OT_outline_remove(bpy.types.Operator):
    bl_idname = "mochitoon.outline_remove"
    bl_label = "Remove Outline"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for ob in _selected_meshes(context):
            core.remove_outline(ob)
        return {"FINISHED"}


classes = (
    MochiToonSettings,
    MOCHITOON_OT_apply,
    MOCHITOON_OT_make_cute,
    MOCHITOON_OT_recolor,
    MOCHITOON_OT_setup_scene,
    MOCHITOON_OT_set_shape,
    MOCHITOON_OT_set_style,
    MOCHITOON_OT_outline_add,
    MOCHITOON_OT_outline_remove,
)


def register():
    _build_items()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mochitoon = bpy.props.PointerProperty(type=MochiToonSettings)


def unregister():
    global _previews
    del bpy.types.Scene.mochitoon
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if _previews is not None:
        bpy.utils.previews.remove(_previews)
        _previews = None
