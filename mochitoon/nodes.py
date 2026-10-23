# SPDX-FileCopyrightText: 2026 東京AI映像合同会社 (Tokyo AI Visuals LLC)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Builds the "MochiToon Core" shader node group.

Layers, bottom to top:
  1. two-tone cel shading with a colored (tinted) shadow
  2. hatching lines inside the shadow, denser where it is darker
  3. rim light on the shadow side
  4. shapes inside the specular highlight: a classic halftone grid, or scattered "stickers".
     Any mix of circle / heart / star / flower / sparkle / moon; each cell picks one at random.
  5. a light rim on the lit side, optionally glowing (bloom from the compositor)

Dots and hatching live in screen space (camera view vector), so they keep the
same size on screen like printed comic screentone. "Stick to Object" shifts the
pattern with the object's origin so it does not swim when the object moves.
"""

import math

import bpy

GROUP_NAME = "MochiToon Core"
GROUP_VERSION = 5

# (key, label, group input) -- each shape is a 0/1 toggle; cells choose among the enabled ones
SHAPES = (("CIRCLE", "Circle", "Circle"), ("HEART", "Heart", "Heart"), ("STAR", "Star", "Star"),
          ("FLOWER", "Flower", "Flower"), ("SPARKLE", "Sparkle", "Sparkle"), ("MOON", "Moon", "Moon"))
STYLES = (("GRID", "Halftone", 0), ("SPRINKLE", "Sprinkle", 1))

# (panel, name, socket type, default, min, max, subtype)
INPUTS = (
    ("Colors", "Base Color", "NodeSocketColor", (1.0, 0.35, 0.58, 1.0), None, None, None),
    ("Colors", "Shadow Tint", "NodeSocketColor", (0.33, 0.19, 1.0, 1.0), None, None, None),
    ("Colors", "Highlight Color", "NodeSocketColor", (1.0, 0.92, 0.89, 1.0), None, None, None),
    ("Colors", "Custom Shadow", "NodeSocketColor", (0.4, 0.2, 0.6, 1.0), None, None, None),
    ("Colors", "Use Custom Shadow", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Colors", "Hatch Color", "NodeSocketColor", (0.1, 0.03, 0.2, 1.0), None, None, None),
    ("Colors", "Auto Hatch Color", "NodeSocketFloat", 1.0, 0.0, 1.0, "FACTOR"),
    ("Colors", "Rim Color", "NodeSocketColor", (1.0, 0.65, 0.82, 1.0), None, None, None),
    ("Colors", "Light Rim Color", "NodeSocketColor", (1.0, 1.0, 1.0, 1.0), None, None, None),
    ("Shading", "Shadow Threshold", "NodeSocketFloat", 0.3, 0.0, 2.0, None),
    ("Shading", "Shadow Softness", "NodeSocketFloat", 0.02, 0.001, 0.5, None),
    ("Dots", "Highlight Size", "NodeSocketFloat", 0.5, 0.0, 1.0, "FACTOR"),
    ("Dots", "Dot Density", "NodeSocketFloat", 130.0, 1.0, 1000.0, None),
    ("Dots", "Dot Angle", "NodeSocketFloat", math.radians(45.0), -math.pi, math.pi, "ANGLE"),
    ("Dots", "Dot Style", "NodeSocketInt", 1, 0, 1, None),
    ("Dots", "Sprinkle Amount", "NodeSocketFloat", 0.3, 0.0, 1.0, "FACTOR"),
    ("Dots", "Size Variation", "NodeSocketFloat", 0.25, 0.0, 1.0, "FACTOR"),
    ("Dots", "Spin", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Shapes", "Circle", "NodeSocketFloat", 1.0, 0.0, 1.0, "FACTOR"),
    ("Shapes", "Heart", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Shapes", "Star", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Shapes", "Flower", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Shapes", "Sparkle", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Shapes", "Moon", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Hatching", "Hatch Amount", "NodeSocketFloat", 0.5, 0.0, 1.0, "FACTOR"),
    ("Hatching", "Hatch Density", "NodeSocketFloat", 140.0, 1.0, 1000.0, None),
    ("Hatching", "Hatch Angle", "NodeSocketFloat", math.radians(-45.0), -math.pi, math.pi, "ANGLE"),
    ("Rim", "Rim Amount", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Rim", "Rim Width", "NodeSocketFloat", 0.25, 0.0, 1.0, "FACTOR"),
    ("Rim", "Light Rim Amount", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Rim", "Light Rim Width", "NodeSocketFloat", 0.18, 0.0, 1.0, "FACTOR"),
    ("Rim", "Glow", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
    ("Pattern", "Stick to Object", "NodeSocketFloat", 0.0, 0.0, 1.0, "FACTOR"),
)

# Soft edge of dots and lines, in pattern cells. EEVEE anti-aliasing does the rest.
EDGE = 0.06


class Builder:
    """Small helper so node math reads like expressions."""

    def __init__(self, tree):
        self.tree = tree
        self.nodes = tree.nodes
        self.links = tree.links
        self.count = 0

    def node(self, bl_idname, **props):
        nd = self.nodes.new(bl_idname)
        for key, value in props.items():
            setattr(nd, key, value)
        # Lay nodes out in a loose grid so the tree is browsable.
        nd.location = (200 * (self.count // 12), -160 * (self.count % 12))
        nd.hide = True
        self.count += 1
        return nd

    def put(self, socket, value):
        if isinstance(value, bpy.types.NodeSocket):
            self.links.new(value, socket)
        elif value is not None:
            socket.default_value = value

    @staticmethod
    def sock(sockets, identifier):
        for s in sockets:
            if s.identifier == identifier:
                return s
        raise KeyError(identifier)

    # scalar math
    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if c is not None:
            self.put(nd.inputs[2], c)
        return nd.outputs[0]

    def add(self, a, b):
        return self.math("ADD", a, b)

    def sub(self, a, b):
        return self.math("SUBTRACT", a, b)

    def mul(self, a, b, clamp=False):
        return self.math("MULTIPLY", a, b, clamp=clamp)

    def div(self, a, b):
        return self.math("DIVIDE", a, b)

    def maxi(self, a, b):
        return self.math("MAXIMUM", a, b)

    def absf(self, a):
        return self.math("ABSOLUTE", a)

    def sqrt(self, a):
        return self.math("SQRT", a)

    def clamp01(self, a):
        return self.math("MULTIPLY", a, 1.0, clamp=True)

    def lerp(self, a, b, t):
        # a + (b - a) * t
        return self.math("MULTIPLY_ADD", self.sub(b, a), t, a)

    def soft_inside(self, signed):
        """signed > 0 inside the shape -> 0..1 mask with a soft edge."""
        return self.math("MULTIPLY_ADD", signed, 1.0 / EDGE, 0.5, clamp=True)

    def length2(self, x, y):
        return self.sqrt(self.add(self.mul(x, x), self.mul(y, y)))

    # vectors
    def combine(self, x, y, z=0.0):
        nd = self.node("ShaderNodeCombineXYZ")
        self.put(nd.inputs[0], x)
        self.put(nd.inputs[1], y)
        self.put(nd.inputs[2], z)
        return nd.outputs[0]

    def separate(self, v):
        nd = self.node("ShaderNodeSeparateXYZ")
        self.put(nd.inputs[0], v)
        return nd.outputs

    def vmath(self, op, a, b=None, scale=None):
        nd = self.node("ShaderNodeVectorMath", operation=op)
        self.put(nd.inputs[0], a)
        if b is not None:
            self.put(nd.inputs[1], b)
        if scale is not None:
            self.put(nd.inputs["Scale"], scale)
        return nd.outputs["Value"] if op in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else nd.outputs["Vector"]

    def rotate_z(self, v, angle):
        nd = self.node("ShaderNodeVectorRotate", rotation_type="Z_AXIS")
        self.put(nd.inputs["Vector"], v)
        self.put(nd.inputs["Angle"], angle)
        return nd.outputs[0]

    def map_range(self, value, from_min, from_max, to_min=0.0, to_max=1.0, smooth=False):
        nd = self.node("ShaderNodeMapRange", data_type="FLOAT",
                       interpolation_type="SMOOTHSTEP" if smooth else "LINEAR", clamp=True)
        self.put(nd.inputs["Value"], value)
        self.put(nd.inputs["From Min"], from_min)
        self.put(nd.inputs["From Max"], from_max)
        self.put(nd.inputs["To Min"], to_min)
        self.put(nd.inputs["To Max"], to_max)
        return nd.outputs["Result"]

    # colors
    def mix(self, a, b, fac, blend="MIX"):
        nd = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend, clamp_factor=True)
        self.put(self.sock(nd.inputs, "Factor_Float"), fac)
        self.put(self.sock(nd.inputs, "A_Color"), a)
        self.put(self.sock(nd.inputs, "B_Color"), b)
        return self.sock(nd.outputs, "Result_Color")

    def hsv(self, color, saturation=1.0, value=1.0):
        nd = self.node("ShaderNodeHueSaturation")
        self.put(nd.inputs["Saturation"], saturation)
        self.put(nd.inputs["Value"], value)
        self.put(nd.inputs["Color"], color)
        return nd.outputs["Color"]

    def white_noise(self, vector):
        """Per-cell random: (value, (r, g, b))."""
        nd = self.node("ShaderNodeTexWhiteNoise", noise_dimensions="3D")
        self.put(nd.inputs["Vector"], vector)
        return nd.outputs["Value"], tuple(self.separate(nd.outputs["Color"]))

    def vmix_scale(self, color, factor):
        """color * factor (factor may exceed 1, for bloom)."""
        nd = self.node("ShaderNodeVectorMath", operation="SCALE")
        self.put(nd.inputs[0], color)
        self.put(nd.inputs["Scale"], factor)
        return nd.outputs["Vector"]

    def light_value(self, bsdf):
        to_rgb = self.node("ShaderNodeShaderToRGB")
        self.put(to_rgb.inputs[0], bsdf)
        bw = self.node("ShaderNodeRGBToBW")
        self.put(bw.inputs[0], to_rgb.outputs["Color"])
        return bw.outputs[0]


def _new_interface(tree):
    panels = {}
    for panel_name, name, stype, default, lo, hi, subtype in INPUTS:
        if panel_name not in panels:
            panels[panel_name] = tree.interface.new_panel(panel_name, default_closed=panel_name not in ("Colors",))
        s = tree.interface.new_socket(name, in_out="INPUT", socket_type=stype, parent=panels[panel_name])
        if subtype:
            s.subtype = subtype
        s.default_value = default
        if lo is not None:
            s.min_value = lo
            s.max_value = hi
    tree.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    tree.interface.new_socket("Color", in_out="OUTPUT", socket_type="NodeSocketColor")


def build_group(tree):
    b = Builder(tree)
    gi = b.node("NodeGroupInput")
    gi.hide = False
    gi.location = (-500, 0)
    go = b.node("NodeGroupOutput")
    go.hide = False
    gi_ = gi.outputs

    # ---- light ---------------------------------------------------------
    diffuse = b.node("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
    light = b.light_value(diffuse.outputs[0])

    glossy_type = "ShaderNodeBsdfGlossy" if hasattr(bpy.types, "ShaderNodeBsdfGlossy") else "ShaderNodeBsdfAnisotropic"
    glossy = b.node(glossy_type)
    glossy.inputs["Color"].default_value = (1, 1, 1, 1)
    glossy.inputs["Roughness"].default_value = 0.5
    spec = b.light_value(glossy.outputs[0])

    thr = gi_["Shadow Threshold"]
    soft = b.maxi(gi_["Shadow Softness"], 0.001)
    # 1 in shadow, 0 in light
    shadow = b.map_range(light, b.sub(thr, soft), b.add(thr, soft), 1.0, 0.0, smooth=True)
    lit = b.math("SUBTRACT", 1.0, shadow)
    # 0 at the terminator, 1 in the darkest part
    darkness = b.clamp01(b.div(b.sub(thr, light), b.maxi(thr, 0.01)))

    # ---- screen-space pattern coordinates ----------------------------------
    cam = b.node("ShaderNodeCameraData")
    vx, vy, vz = b.separate(cam.outputs["View Vector"])
    depth = b.maxi(b.absf(vz), 1e-4)
    sx = b.div(vx, depth)
    sy = b.div(vy, depth)

    obj = b.node("ShaderNodeObjectInfo")
    to_cam = b.node("ShaderNodeVectorTransform", vector_type="POINT", convert_from="WORLD", convert_to="CAMERA")
    b.put(to_cam.inputs[0], obj.outputs["Location"])
    ox, oy, oz = b.separate(to_cam.outputs[0])
    odepth = b.maxi(b.absf(oz), 1e-4)
    stick = gi_["Stick to Object"]
    sx = b.sub(sx, b.mul(b.div(ox, odepth), stick))
    sy = b.sub(sy, b.mul(b.div(oy, odepth), stick))
    screen = b.combine(sx, sy)

    # ---- halftone dots in the highlight ----------------------------------
    size = gi_["Highlight Size"]
    # Highlight Size 0 -> only the very peak, 1 -> a wide glossy area
    # Glossy peaks around 10+, so work on sqrt(spec) to get a long big-to-small dot gradient.
    spec = b.sqrt(b.maxi(spec, 0.0))
    spec_lo = b.lerp(1.2, 0.2, size)
    hi = b.mul(b.map_range(spec, spec_lo, b.add(spec_lo, 1.4)), lit)
    has_dot = b.math("GREATER_THAN", hi, 0.02)

    angle = gi_["Dot Angle"]
    style = gi_["Dot Style"]  # 0 halftone grid, 1 sprinkle
    # stickers want bigger cells than a halftone grid: sprinkle uses ~0.28 x the density
    density = b.mul(gi_["Dot Density"], b.math("MULTIPLY_ADD", style, -0.72, 1.0))
    grid = b.rotate_z(b.vmath("SCALE", screen, scale=density), angle)
    cell = b.vmath("FLOOR", grid)
    rnd1 = b.white_noise(cell)                               # value + 3 channels per cell
    rnd2 = b.white_noise(b.vmath("ADD", cell, (17.3, 5.1, 0.0)))
    r_pick, (r_spin, r_jx, r_jy) = rnd1
    r_keep, (r_size, _, _) = rnd2

    q = b.vmath("SUBTRACT", b.vmath("FRACTION", grid), (0.5, 0.5, 0.0))
    # sprinkle: nudge each sticker off the grid so it doesn't read as a pattern
    jitter = b.mul(style, 0.16)
    q = b.vmath("SUBTRACT", q, b.combine(b.mul(b.sub(r_jx, 0.5), jitter), b.mul(b.sub(r_jy, 0.5), jitter)))
    spin = b.mul(b.mul(b.sub(r_spin, 0.5), 2 * math.pi), gi_["Spin"])
    q = b.rotate_z(q, b.sub(spin, angle))  # upright (unless Spin), whatever the grid angle
    qx, qy, _ = b.separate(q)

    # halftone: size follows the glossy highlight; sprinkle: full-size stickers over the lit side
    # (Highlight Size widens the lit area they may land on; the edge is tight so few stickers get cut)
    r_grid = b.mul(b.sqrt(hi), 0.56)
    spr_lo = b.add(thr, b.lerp(0.55, 0.06, size))
    spr_zone = b.mul(b.map_range(light, spr_lo, b.add(spr_lo, 0.06), smooth=True), lit)
    r_spr = b.mul(b.maxi(spr_zone, b.math("GREATER_THAN", hi, 0.3)), 0.4)
    has_dot = b.maxi(has_dot, b.mul(style, b.math("GREATER_THAN", r_spr, 0.01)))
    r = b.lerp(r_grid, r_spr, style)
    r = b.mul(r, b.math("MULTIPLY_ADD", r_size, b.mul(gi_["Size Variation"], -1.0), 1.0))
    r = b.math("MINIMUM", r, 0.42)  # neighbours never merge into a sheet
    keep = b.lerp(1.0, b.math("LESS_THAN", r_keep, gi_["Sprinkle Amount"]), style)

    qlen = b.length2(qx, qy)
    s_circle = b.sub(r, qlen)

    ax, ay = b.absf(qx), b.absf(qy)
    astroid = b.math("POWER", b.add(b.sqrt(ax), b.sqrt(ay)), 2.0)
    s_sparkle = b.sub(b.math("MINIMUM", b.mul(r, 1.45), 0.47), astroid)

    k = b.maxi(b.mul(r, 1.3), 1e-4)
    nx, ny = b.div(qx, k), b.div(qy, k)
    lobe1 = b.sub(0.45, b.length2(b.add(nx, 0.35), b.sub(ny, 0.2)))
    lobe2 = b.sub(0.45, b.length2(b.sub(nx, 0.35), b.sub(ny, 0.2)))
    tip = b.mul(b.sub(0.65, b.add(b.absf(nx), b.absf(b.add(ny, 0.15)))), 0.71)
    s_heart = b.mul(b.maxi(b.maxi(lobe1, lobe2), tip), k)

    # polar shapes: 5-point star and 5-petal flower, one tip pointing up
    a_pol = b.math("ARCTAN2", qy, qx)
    arm = b.math("FRACT", b.math("MULTIPLY_ADD", b.sub(a_pol, math.pi / 2), 5 / (2 * math.pi), 0.5))
    d_arm = b.mul(b.absf(b.sub(arm, 0.5)), 2.0)                # 0 on a tip, 1 between tips
    s_star = b.mul(b.sub(b.mul(r, b.math("MULTIPLY_ADD", d_arm, -0.55, 1.18)), qlen), 0.8)
    petal = b.absf(b.math("COSINE", b.mul(b.sub(a_pol, math.pi / 2), 2.5)))
    s_flower = b.mul(b.sub(b.mul(r, b.math("MULTIPLY_ADD", petal, 0.48, 0.66)), qlen), 0.85)
    # flower centre: a small hole so it reads as a flower, not a blob
    s_flower = b.math("MINIMUM", s_flower, b.sub(qlen, b.mul(r, 0.22)))

    bite = b.length2(b.sub(qx, b.mul(r, 0.42)), b.sub(qy, b.mul(r, 0.25)))
    s_moon = b.math("MINIMUM", s_circle, b.sub(bite, b.mul(r, 0.82)))

    sdfs = {"Circle": s_circle, "Heart": s_heart, "Star": s_star, "Flower": s_flower,
            "Sparkle": s_sparkle, "Moon": s_moon}
    # each cell picks one of the enabled shapes (equal odds)
    weights = [b.math("GREATER_THAN", gi_[name], 0.5) for name in sdfs]
    total = weights[0]
    for w in weights[1:]:
        total = b.add(total, w)
    t = b.mul(r_pick, total)
    acc = 0.0
    s_dot = None
    for w, sdf in zip(weights, sdfs.values()):
        lo = acc
        acc = b.add(acc, w)
        sel = b.mul(w, b.mul(b.math("GREATER_THAN", b.add(t, 1e-4), lo), b.math("LESS_THAN", t, acc)))
        term = b.mul(sel, sdf)
        s_dot = term if s_dot is None else b.add(s_dot, term)
    any_shape = b.math("GREATER_THAN", total, 0.5)
    dots = b.mul(b.mul(b.mul(b.soft_inside(s_dot), has_dot), keep), any_shape)

    # ---- hatching in the shadow ------------------------------------------
    hgrid = b.rotate_z(b.vmath("SCALE", screen, scale=gi_["Hatch Density"]), gi_["Hatch Angle"])
    hx, _, _ = b.separate(hgrid)
    line_dist = b.absf(b.sub(b.math("FRACT", hx), 0.5))
    cover = b.mul(gi_["Hatch Amount"], b.math("MULTIPLY_ADD", darkness, 0.7, 0.3))
    hatch = b.soft_inside(b.sub(b.mul(cover, 0.5), line_dist))
    hatch = b.mul(b.mul(hatch, shadow), b.math("GREATER_THAN", cover, 0.01))

    # ---- rim light on the shadow side ------------------------------------
    weight = b.node("ShaderNodeLayerWeight")
    weight.inputs["Blend"].default_value = 0.5
    edge_start = b.math("SUBTRACT", 1.0, gi_["Rim Width"])
    rim = b.map_range(weight.outputs["Facing"], edge_start, b.add(edge_start, 0.04), smooth=True)
    rim = b.mul(b.mul(rim, shadow), gi_["Rim Amount"])
    # light rim: silhouette x light arriving there. The normal is bent away from the camera, so a light
    # behind the object (back light) still lights the rim: that is the bright "kira" edge of anime.
    geo = b.node("ShaderNodeNewGeometry")
    bent = b.vmath("NORMALIZE", b.vmath("SUBTRACT", geo.outputs["Normal"], b.vmath("SCALE", geo.outputs["Incoming"], scale=0.85)))
    rim_diffuse = b.node("ShaderNodeBsdfDiffuse")
    rim_diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
    b.put(rim_diffuse.inputs["Normal"], bent)
    rim_light = b.map_range(b.light_value(rim_diffuse.outputs[0]), 0.08, 0.3, smooth=True)
    l_start = b.math("SUBTRACT", 1.0, gi_["Light Rim Width"])
    lrim = b.map_range(weight.outputs["Facing"], l_start, b.add(l_start, 0.03), smooth=True)
    lrim = b.mul(b.mul(lrim, rim_light), gi_["Light Rim Amount"])

    # ---- colors -----------------------------------------------------------
    base = gi_["Base Color"]
    tint = gi_["Shadow Tint"]
    auto_shadow = b.hsv(b.mix(base, tint, 1.0, blend="MULTIPLY"), saturation=1.0, value=1.0)
    shadow_col = b.mix(auto_shadow, gi_["Custom Shadow"], gi_["Use Custom Shadow"])
    auto_hatch = b.hsv(b.mix(shadow_col, tint, 1.0, blend="MULTIPLY"), saturation=1.1, value=0.7)
    hatch_col = b.mix(gi_["Hatch Color"], auto_hatch, gi_["Auto Hatch Color"])

    col = b.mix(base, shadow_col, shadow)
    col = b.mix(col, hatch_col, hatch)
    col = b.mix(col, gi_["Rim Color"], rim)
    # Glow pushes the rim (and a little of the dots) above 1.0 so the compositor bloom catches only them
    glow = gi_["Glow"]
    dot_col = b.vmix_scale(gi_["Highlight Color"], b.math("MULTIPLY_ADD", glow, 0.6, 1.0))
    col = b.mix(col, dot_col, dots)
    lrim_col = b.vmix_scale(gi_["Light Rim Color"], b.math("MULTIPLY_ADD", glow, 2.5, 1.0))
    col = b.mix(col, lrim_col, lrim)

    emit = b.node("ShaderNodeEmission")
    b.put(emit.inputs["Color"], col)
    emit.inputs["Strength"].default_value = 1.0
    b.put(go.inputs["Shader"], emit.outputs[0])
    b.put(go.inputs["Color"], col)
    go.location = (200 * (b.count // 12 + 1), 0)


def ensure_group():
    tree = bpy.data.node_groups.get(GROUP_NAME)
    if tree is not None and tree.get("mochitoon_version", 0) >= GROUP_VERSION:
        return tree
    if tree is None:
        tree = bpy.data.node_groups.new(GROUP_NAME, "ShaderNodeTree")
    else:
        _upgrade(tree)
        return tree
    _new_interface(tree)
    build_group(tree)
    tree["mochitoon_version"] = GROUP_VERSION
    return tree


def _upgrade(tree):
    """Older build: new interface + inside, carrying over every value the materials had set."""
    users = []
    for mat in bpy.data.materials:
        if mat.node_tree is None:
            continue
        for nd in mat.node_tree.nodes:
            if nd.type == "GROUP" and nd.node_tree == tree:
                vals = {s.name: (tuple(s.default_value) if hasattr(s.default_value, "__len__") else s.default_value)
                        for s in nd.inputs if hasattr(s, "default_value")}
                links = [(l.from_socket, l.to_socket.name) for l in mat.node_tree.links if l.to_node == nd]
                outs = [(l.from_socket.name, l.to_socket) for l in mat.node_tree.links if l.from_node == nd]
                users.append((mat, nd, vals, links, outs))
    old_shape = {"Circle": 0, "Heart": 1, "Sparkle": 2}
    tree.interface.clear()
    tree.nodes.clear()
    _new_interface(tree)
    build_group(tree)
    tree["mochitoon_version"] = GROUP_VERSION
    for mat, nd, vals, links, outs in users:
        for name, v in vals.items():
            sock = nd.inputs.get(name)
            if sock is not None:
                try:
                    sock.default_value = v
                except (TypeError, ValueError):
                    pass
        if "Dot Shape" in vals:  # v2 had one int shape
            for name, idx in old_shape.items():
                nd.inputs[name].default_value = 1.0 if vals["Dot Shape"] == idx else 0.0
        for from_sock, to_name in links:
            if nd.inputs.get(to_name) is not None:
                mat.node_tree.links.new(from_sock, nd.inputs[to_name])
        for from_name, to_sock in outs:
            if nd.outputs.get(from_name) is not None:
                mat.node_tree.links.new(nd.outputs[from_name], to_sock)


def find_core_node(material):
    if material is None or material.node_tree is None:
        return None
    for nd in material.node_tree.nodes:
        if nd.type == "GROUP" and nd.node_tree is not None and nd.node_tree.name.startswith(GROUP_NAME):
            return nd
    return None
