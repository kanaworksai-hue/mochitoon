# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import core, nodes


def _core_node(context):
    ob = context.object
    return nodes.find_core_node(ob.active_material) if ob else None


def _prop(layout, node, name, text=None):
    sock = node.inputs.get(name)
    if sock is not None:
        layout.prop(sock, "default_value", text=text or name)


class MochiToonPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MochiToon"


class MOCHITOON_PT_main(MochiToonPanel, bpy.types.Panel):
    bl_label = "MochiToon"

    def draw(self, context):
        layout = self.layout
        s = context.scene.mochitoon
        layout.template_icon_view(s, "palette", show_labels=True, scale=6.0, scale_popup=4.0)
        col = layout.column(align=True)
        col.prop(s, "keep_colors", text="Keep Object Colors / Textures")
        col.prop(s, "with_outline")
        row = layout.row()
        row.scale_y = 1.6
        row.operator("mochitoon.apply", icon="SHADING_RENDERED")
        row = layout.row(align=True)
        row.operator("mochitoon.recolor", icon="COLOR")
        row.operator("mochitoon.setup_scene", icon="LIGHT_SUN")
        if context.scene.view_settings.view_transform != "Standard":
            box = layout.box()
            box.label(text="Colors look washed out?", icon="INFO")
            box.label(text="'Setup Cute Scene' sets View to Standard")


class MOCHITOON_PT_look(MochiToonPanel, bpy.types.Panel):
    bl_label = "Look"
    bl_parent_id = "MOCHITOON_PT_main"

    @classmethod
    def poll(cls, context):
        return _core_node(context) is not None

    def draw(self, context):
        layout = self.layout
        node = _core_node(context)
        layout.label(text=context.object.active_material.name, icon="MATERIAL")

        col = layout.column(align=True)
        tex = core.base_texture_node(context.object.active_material)
        if tex is not None:
            col.label(text=f"Base: {tex.image.name if tex.image else 'texture'}", icon="IMAGE_DATA")
        else:
            _prop(col, node, "Base Color", "Base")
        _prop(col, node, "Shadow Tint", "Shadow Tint")
        _prop(col, node, "Highlight Color", "Dots")
        row = col.row(align=True)
        _prop(row, node, "Use Custom Shadow", "Custom Shadow")
        if node.inputs["Use Custom Shadow"].default_value > 0.0:
            _prop(col, node, "Custom Shadow", "Shadow")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Shadow")
        _prop(col, node, "Shadow Threshold", "Size")
        _prop(col, node, "Shadow Softness", "Softness")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Highlight Shapes")
        style = node.inputs["Dot Style"].default_value
        row = col.row(align=True)
        for key, label, value in nodes.STYLES:
            op = row.operator("mochitoon.set_style", text=label, depress=(style == value))
            op.style = value
        on = set(core.enabled_shapes(node))
        grid = col.grid_flow(columns=3, align=True)
        for key, label, _ in nodes.SHAPES:
            op = grid.operator("mochitoon.set_shape", text=label, depress=(key in on))
            op.shape = key
        if style == 1:
            _prop(col, node, "Sprinkle Amount", "Amount")
        _prop(col, node, "Highlight Size", "Size")
        _prop(col, node, "Dot Density", "Density")
        _prop(col, node, "Size Variation", "Size Variation")
        _prop(col, node, "Spin", "Spin")
        _prop(col, node, "Dot Angle", "Angle")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Hatching")
        _prop(col, node, "Hatch Amount", "Amount")
        _prop(col, node, "Hatch Density", "Density")
        _prop(col, node, "Hatch Angle", "Angle")
        _prop(col, node, "Auto Hatch Color", "Auto Color")
        if node.inputs["Auto Hatch Color"].default_value < 1.0:
            _prop(col, node, "Hatch Color", "Color")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Rim Lights")
        _prop(col, node, "Rim Amount", "Amount")
        _prop(col, node, "Rim Width", "Width")
        _prop(col, node, "Rim Color", "Color")
        col.separator()
        _prop(col, node, "Light Rim Amount", "Light Rim")
        _prop(col, node, "Light Rim Width", "Width")
        _prop(col, node, "Light Rim Color", "Color")
        _prop(col, node, "Glow", "Glow")

        layout.separator()
        _prop(layout, node, "Stick to Object")


class MOCHITOON_PT_outline(MochiToonPanel, bpy.types.Panel):
    bl_label = "Outline"
    bl_parent_id = "MOCHITOON_PT_main"

    def draw(self, context):
        layout = self.layout
        s = context.scene.mochitoon
        layout.prop(s, "outline_width", text="Width")
        ob = context.object
        if ob is not None and ob.type == "MESH":
            line = next((m for m in ob.data.materials if core.is_line(m)), None)
            if line is not None:
                sock = core.line_color(line)
                if sock is not None:
                    layout.prop(sock, "default_value", text="Color")
        row = layout.row(align=True)
        row.operator("mochitoon.outline_add", icon="ADD")
        row.operator("mochitoon.outline_remove", icon="REMOVE")


classes = (MOCHITOON_PT_main, MOCHITOON_PT_look, MOCHITOON_PT_outline)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
