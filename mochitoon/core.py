# SPDX-License-Identifier: GPL-3.0-or-later
"""Materials, outlines and scene setup. No UI here, so tests can call it directly."""

import math
import re

import bpy

from . import nodes
from .palettes import PALETTES, hex_to_linear

OUTLINE_MOD = "MochiToon Outline"
OUTLINE_MAT_PREFIX = "MochiToon Line"
MAT_PREFIX = "MochiToon"


LEGACY_SHAPES = ("CIRCLE", "HEART", "SPARKLE")  # the old int "Dot Shape"


def parse_shapes(shapes):
    """'HEART', 'star+flower', ['STAR', 'MOON'], 1 (legacy int) -> set of shape keys."""
    if shapes is None:
        return None
    if isinstance(shapes, int):
        return {LEGACY_SHAPES[min(max(shapes, 0), 2)]}
    if isinstance(shapes, str):
        shapes = re.split(r"[+,/ ]+", shapes.strip())
    keys = {str(x).strip().upper() for x in shapes if str(x).strip()}
    valid = {k for k, _, _ in nodes.SHAPES}
    bad = keys - valid
    if bad:
        raise ValueError(f"Unknown shape(s) {sorted(bad)}. Choose from: {', '.join(k for k, _, _ in nodes.SHAPES)}")
    return keys


def set_shapes(core_node, shapes):
    keys = parse_shapes(shapes)
    if keys is None:
        return
    for key, _, name in nodes.SHAPES:
        set_input(core_node, name, 1.0 if key in keys else 0.0)


def enabled_shapes(core_node):
    return [key for key, _, name in nodes.SHAPES if core_node.inputs[name].default_value > 0.5]


def set_input(core_node, name, value):
    sock = core_node.inputs.get(name)
    if sock is not None:
        sock.default_value = value


def apply_palette(core_node, key, keep_base=False):
    pal = PALETTES[key]
    if not keep_base:
        set_input(core_node, "Base Color", hex_to_linear(pal["base"]))
    set_input(core_node, "Shadow Tint", hex_to_linear(pal["tint"]))
    set_input(core_node, "Highlight Color", hex_to_linear(pal["highlight"]))
    set_input(core_node, "Rim Color", hex_to_linear(pal["rim"]))
    set_input(core_node, "Use Custom Shadow", 0.0)
    if pal["hatch"]:
        set_input(core_node, "Hatch Color", hex_to_linear(pal["hatch"]))
        set_input(core_node, "Auto Hatch Color", 0.0)
    else:
        set_input(core_node, "Auto Hatch Color", 1.0)
    # reset the palette-controlled settings to group defaults, then apply overrides
    defaults = {name: default for _, name, _, default, *_ in nodes.INPUTS}
    for name in ("Rim Amount", "Rim Width", "Hatch Amount", "Dot Density"):
        set_input(core_node, name, defaults[name])
    for name, value in pal["settings"].items():
        set_input(core_node, name, value)
    tree = core_node.id_data
    for m in bpy.data.materials:
        if m.node_tree == tree:
            m["mochitoon_palette"] = key
            m.diffuse_color = core_node.inputs["Base Color"].default_value


def original_base_color(material):
    """Best guess of a material's visible color, in linear RGBA."""
    if material is None:
        return None
    core = nodes.find_core_node(material)
    if core is not None:
        return tuple(core.inputs["Base Color"].default_value)
    if material.node_tree is not None:
        for nd in material.node_tree.nodes:
            if nd.type in ("BSDF_PRINCIPLED", "BSDF_DIFFUSE", "EMISSION"):
                sock = nd.inputs.get("Base Color") or nd.inputs.get("Color")
                if sock is not None and not sock.is_linked:
                    return tuple(sock.default_value)
    return tuple(material.diffuse_color)


def base_color_texture(material):
    """The image feeding a material's base color, if any (searches a few nodes upstream)."""
    if material is None or material.node_tree is None or nodes.find_core_node(material) is not None:
        return None
    for nd in material.node_tree.nodes:
        if nd.type not in ("BSDF_PRINCIPLED", "BSDF_DIFFUSE", "EMISSION"):
            continue
        sock = nd.inputs.get("Base Color") or nd.inputs.get("Color")
        if sock is None or not sock.is_linked:
            continue
        todo, seen = [sock.links[0].from_node], set()
        while todo and len(seen) < 16:
            up = todo.pop(0)
            if up.name in seen:
                continue
            seen.add(up.name)
            if up.type == "TEX_IMAGE" and up.image is not None:
                return up
            todo.extend(link.from_node for inp in up.inputs for link in inp.links)
    return None


def link_base_texture(material, tex_node):
    """Copy an image texture node into a MochiToon material and drive Base Color with it."""
    tree = material.node_tree
    core_node = nodes.find_core_node(material)
    tex = tree.nodes.new("ShaderNodeTexImage")
    tex.image = tex_node.image
    tex.interpolation = tex_node.interpolation
    tex.extension = tex_node.extension
    tex.location = (-320, 0)
    tex.label = "Base Texture"
    vec = tex_node.inputs["Vector"]
    if vec.is_linked and vec.links[0].from_node.type == "UVMAP":
        uv = tree.nodes.new("ShaderNodeUVMap")
        uv.uv_map = vec.links[0].from_node.uv_map
        uv.location = (-520, 0)
        tree.links.new(uv.outputs[0], tex.inputs["Vector"])
    tree.links.new(tex.outputs["Color"], core_node.inputs["Base Color"])
    return tex


def base_texture_node(material):
    core_node = nodes.find_core_node(material)
    if core_node is None:
        return None
    sock = core_node.inputs["Base Color"]
    if sock.is_linked and sock.links[0].from_node.type == "TEX_IMAGE":
        return sock.links[0].from_node
    return None


def new_material(name, palette_key, base=None, texture=None):
    group = nodes.ensure_group()
    mat = bpy.data.materials.new(name)
    if hasattr(mat, "use_nodes") and not mat.use_nodes:
        mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    core = tree.nodes.new("ShaderNodeGroup")
    core.node_tree = group
    core.location = (0, 0)
    core.width = 220
    tree.links.new(core.outputs["Shader"], out.inputs["Surface"])
    mat["mochitoon"] = True
    apply_palette(core, palette_key)
    if base is not None:
        set_input(core, "Base Color", base)
        mat.diffuse_color = base
    if texture is not None:
        link_base_texture(mat, texture)
    return mat


def is_mochi(material):
    return material is not None and material.get("mochitoon", False)


def is_line(material):
    return material is not None and material.get("mochitoon_line", False)


def smooth_by_angle(mesh, degrees=40.0):
    """Smooth fully flat-shaded meshes (fresh primitives) but keep hard edges like a cube's.
    Meshes that already have any smooth shading are left exactly as the user made them."""
    if any(p.use_smooth for p in mesh.polygons):
        return
    if hasattr(mesh, "shade_smooth") and hasattr(mesh, "set_sharp_from_angle"):
        mesh.shade_smooth()
        mesh.set_sharp_from_angle(angle=math.radians(degrees))
    else:
        for poly in mesh.polygons:
            poly.use_smooth = True


def apply_to_objects(objects, palette_key, keep_colors=False):
    """Give each mesh a MochiToon material. Returns how many objects changed."""
    nodes.ensure_group()  # upgrades an older group in this file, keeping its values
    shared = None
    converted = {}
    changed = 0
    for ob in objects:
        if ob.type not in {"MESH", "CURVE", "SURFACE", "META", "FONT"}:
            continue
        changed += 1
        if ob.type == "MESH":
            smooth_by_angle(ob.data)
        slots = [s for s in ob.material_slots if not is_line(s.material)]
        if keep_colors and slots:
            for slot in slots:
                src = slot.material
                if is_mochi(src):
                    apply_palette(nodes.find_core_node(src), palette_key, keep_base=True)
                    continue
                if src not in converted:
                    base = original_base_color(src)
                    name = f"{MAT_PREFIX} {src.name if src else palette_key.title()}"
                    converted[src] = new_material(name, palette_key, base, base_color_texture(src))
                slot.material = converted[src]
            continue
        if shared is None:
            shared = new_material(f"{MAT_PREFIX} {PALETTES[palette_key]['label']}", palette_key)
        if not slots:
            ob.data.materials.append(shared)
        for slot in slots:
            slot.material = shared
        _move_line_slot_last(ob)
    return changed


def outline_material(color_linear, key="Custom"):
    name = f"{OUTLINE_MAT_PREFIX} {key}"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        if hasattr(mat, "use_nodes") and not mat.use_nodes:
            mat.use_nodes = True
        tree = mat.node_tree
        tree.nodes.clear()
        out = tree.nodes.new("ShaderNodeOutputMaterial")
        emit = tree.nodes.new("ShaderNodeEmission")
        emit.location = (-250, 0)
        tree.links.new(emit.outputs[0], out.inputs["Surface"])
        mat.use_backface_culling = True
        if hasattr(mat, "use_backface_culling_shadow"):
            mat.use_backface_culling_shadow = True
        mat["mochitoon_line"] = True
    emit = next(n for n in mat.node_tree.nodes if n.type == "EMISSION")
    emit.inputs["Color"].default_value = color_linear
    mat.diffuse_color = color_linear
    return mat


def line_color(material):
    emit = next((n for n in material.node_tree.nodes if n.type == "EMISSION"), None)
    return emit.inputs["Color"] if emit else None


def _move_line_slot_last(ob):
    mesh = ob.data
    if not hasattr(mesh, "materials"):
        return
    idx = next((i for i, m in enumerate(mesh.materials) if is_line(m)), None)
    if idx is None or idx == len(mesh.materials) - 1:
        return
    line = mesh.materials.pop(index=idx)
    mesh.materials.append(line)


def add_outline(ob, thickness, line_mat):
    if ob.type != "MESH":
        return False
    mesh = ob.data
    if not any(is_line(m) for m in mesh.materials):
        if len(mesh.materials) == 0:
            mesh.materials.append(None)
        mesh.materials.append(line_mat)
    else:
        for i, m in enumerate(mesh.materials):
            if is_line(m):
                mesh.materials[i] = line_mat
    _move_line_slot_last(ob)
    mod = ob.modifiers.get(OUTLINE_MOD)
    if mod is None:
        mod = ob.modifiers.new(OUTLINE_MOD, "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    # even offset shoots spikes out of degenerate vertices on scanned/AI-generated meshes
    mod.use_even_offset = False
    mod.use_quality_normals = True
    mod.material_offset = len(mesh.materials) - 1
    mod.show_in_editmode = False
    return True


def remove_outline(ob):
    mod = ob.modifiers.get(OUTLINE_MOD)
    if mod is not None:
        ob.modifiers.remove(mod)
    if ob.type == "MESH":
        mesh = ob.data
        for i in reversed(range(len(mesh.materials))):
            if is_line(mesh.materials[i]):
                mesh.materials.pop(index=i)


def outline_thickness_for(ob, relative):
    """Outline width as a fraction of the object's size, so tiny and huge objects both look right."""
    dims = [d / max(s, 1e-6) for d, s in zip(ob.dimensions, ob.scale)]
    size = sum(dims) / 3.0 if dims else 1.0
    return max(size * relative, 1e-4)


def _set_enum(owner, prop, wanted):
    try:
        setattr(owner, prop, wanted)
        return True
    except TypeError:
        return False


def setup_viewports(screen):
    """Material Preview, but lit by the scene sun and world so the toon bands match the render."""
    for area in screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type == "VIEW_3D":
                if space.shading.type in {"SOLID", "WIREFRAME"}:
                    space.shading.type = "MATERIAL"
                space.shading.use_scene_lights = True
                space.shading.use_scene_world = True


def setup_scene(scene, palette_key):
    """EEVEE + exact colors + a crisp sun + flat background."""
    pal = PALETTES[palette_key]
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if _set_enum(scene.render, "engine", engine):
            break
    # AgX/Filmic wash out candy colors; Standard shows exactly what you pick.
    _set_enum(scene.view_settings, "view_transform", "Standard")
    _set_enum(scene.view_settings, "look", "None")
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    sun = next((o for o in scene.objects if o.type == "LIGHT" and o.data.type == "SUN"), None)
    if sun is None:
        data = bpy.data.lights.new("MochiToon Sun", "SUN")
        sun = bpy.data.objects.new("MochiToon Sun", data)
        scene.collection.objects.link(sun)
        sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    # EEVEE diffuse = strength * cos / pi, so pi makes the light value read as plain cos(angle)
    sun.data.energy = math.pi
    sun.data.color = (1.0, 1.0, 1.0)
    sun.data.angle = math.radians(1.0)
    if hasattr(sun.data, "use_shadow"):
        sun.data.use_shadow = True
    # crisp toon terminators instead of blurry shadow-map edges
    if hasattr(sun.data, "shadow_filter_radius"):
        sun.data.shadow_filter_radius = 0.0
    if hasattr(sun.data, "use_shadow_jitter"):
        sun.data.use_shadow_jitter = False

    world = scene.world or bpy.data.worlds.new("MochiToon World")
    scene.world = world
    if hasattr(world, "use_nodes") and not world.use_nodes:
        world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()
    out = tree.nodes.new("ShaderNodeOutputWorld")
    out.location = (400, 0)
    seen = tree.nodes.new("ShaderNodeBackground")
    seen.location = (0, 100)
    seen.inputs["Color"].default_value = hex_to_linear(pal["bg"])
    ambient = tree.nodes.new("ShaderNodeBackground")
    ambient.location = (0, -100)
    ambient.inputs["Color"].default_value = (1, 1, 1, 1)
    ambient.inputs["Strength"].default_value = 0.08
    path = tree.nodes.new("ShaderNodeLightPath")
    path.location = (0, 300)
    mix = tree.nodes.new("ShaderNodeMixShader")
    mix.location = (200, 0)
    tree.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    tree.links.new(ambient.outputs[0], mix.inputs[1])
    tree.links.new(seen.outputs[0], mix.inputs[2])
    tree.links.new(mix.outputs[0], out.inputs["Surface"])
    setup_bloom(scene)
    return sun


def setup_bloom(scene, strength=0.9):
    """Compositor bloom that only catches values above 1.0 (the Glow-boosted rims and dots)."""
    if not hasattr(scene, "compositing_node_group"):
        return None
    ng = bpy.data.node_groups.get("MochiToon Bloom")
    if ng is None:
        ng = bpy.data.node_groups.new("MochiToon Bloom", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        rl = ng.nodes.new("CompositorNodeRLayers")
        glare = ng.nodes.new("CompositorNodeGlare")
        glare.location = (300, 0)
        out = ng.nodes.new("NodeGroupOutput")
        out.location = (600, 0)
        glare.inputs["Type"].default_value = "Bloom"
        glare.inputs["Quality"].default_value = "High"
        glare.inputs["Threshold"].default_value = 1.0
        glare.inputs["Size"].default_value = 0.6
        ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
        ng.links.new(glare.outputs["Image"], out.inputs[0])
    glare = next(n for n in ng.nodes if n.bl_idname == "CompositorNodeGlare")
    glare.inputs["Strength"].default_value = strength
    scene.compositing_node_group = ng
    if hasattr(scene.render, "use_compositing"):
        scene.render.use_compositing = True
    return ng
