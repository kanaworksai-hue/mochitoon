# SPDX-FileCopyrightText: 2026 東京AI映像合同会社 (Tokyo AI Visuals LLC)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Cute color palettes.

Colors are written as sRGB hex (what you see in a color picker) and converted
to linear when they are put into Blender sockets.
"""

# Each palette:
#   base       main surface color
#   tint       multiplied into base to get the shadow color (the "colored shadow" trick)
#   highlight  color of the halftone dots in the lit area
#   hatch      color of the hatching lines (None = automatic, a deeper shadow)
#   rim        color of the rim light on the shadow side
#   line       outline color
#   bg         background color for "Setup Cute Scene"
#   settings   extra group-input overrides
PALETTES = {
    "SAKURA": dict(
        label="Sakura", description="Pink with lilac shadows",
        base="#FF9FC8", tint="#B394FF", highlight="#FFF6F2", hatch=None,
        rim="#FFD3EA", line="#2A0E3A", bg="#FCE8F1",
        settings={},
    ),
    "LEMON": dict(
        label="Lemon", description="Lemon yellow with orange shadows",
        base="#FFE04A", tint="#FF8A5C", highlight="#FFFFFF", hatch=None,
        rim="#FFF6B8", line="#3A1A08", bg="#8ED3FF",
        settings={},
    ),
    "MINT": dict(
        label="Mint", description="Mint green with teal-blue shadows",
        base="#8EF2C8", tint="#5C8CF2", highlight="#FFFFFF", hatch=None,
        rim="#DFFFF0", line="#0C2A33", bg="#FFF1D6",
        settings={},
    ),
    "SODA": dict(
        label="Soda", description="Sky blue with violet shadows",
        base="#7FD0FF", tint="#8C72FF", highlight="#FFFFFF", hatch=None,
        rim="#D8F3FF", line="#101A44", bg="#FFE3EE",
        settings={},
    ),
    "GRAPE": dict(
        label="Grape", description="Lavender with deep purple shadows",
        base="#BB8CFF", tint="#8A5ED6", highlight="#FFE8FF", hatch=None,
        rim="#EBD8FF", line="#1E0A36", bg="#D7F7EC",
        settings={},
    ),
    "PEACH": dict(
        label="Peach", description="Peach with rosy shadows",
        base="#FFB48C", tint="#F07A9A", highlight="#FFFAF0", hatch=None,
        rim="#FFE4D2", line="#3A1418", bg="#E6F0FF",
        settings={},
    ),
    "MELON": dict(
        label="Melon", description="Lime with green-teal shadows",
        base="#C4FF5A", tint="#4FB88E", highlight="#FFFFFF", hatch=None,
        rim="#F0FFC8", line="#0E2A14", bg="#B98CFF",
        settings={},
    ),
    "COMIC": dict(
        label="Comic", description="Classic comic red, black ink",
        base="#FF3B4A", tint="#7050B8", highlight="#FFF4C8", hatch="#3A0A24",
        rim="#FFB0B8", line="#000000", bg="#FFE45C",
        settings={"Dot Density": 100.0},
    ),
    "NEON_NIGHT": dict(
        label="Neon Night", description="Black cat with neon purple glow",
        base="#151020", tint="#5A3A8A", highlight="#FF7CF0", hatch="#B23BFF",
        rim="#C04BFF", line="#B23BFF", bg="#2A2A30",
        settings={"Rim Amount": 1.0, "Rim Width": 0.3, "Hatch Amount": 0.65},
    ),
    "CHOCO": dict(
        label="Choco", description="Milk chocolate with plum shadows",
        base="#B57A5C", tint="#8A5E9A", highlight="#FFE8D0", hatch=None,
        rim="#E8C0A8", line="#24100A", bg="#FFD6E4",
        settings={},
    ),
    # Halloween
    "PUMPKIN": dict(
        label="Pumpkin", description="Pumpkin orange with purple shadows",
        base="#FF9A3C", tint="#8A4FD8", highlight="#FFF3B0", hatch="#3A1250",
        rim="#FFD27A", line="#2A0E3A", bg="#2B1B3D",
        settings={"Rim Amount": 0.6},
    ),
    "GHOST": dict(
        label="Ghost", description="Ghost white with lilac shadows and an icy rim",
        base="#F4F1FF", tint="#9C8CFF", highlight="#FFFFFF", hatch=None,
        rim="#B8F0FF", line="#2A1E4A", bg="#3A2D5C",
        settings={"Rim Amount": 0.8},
    ),
    "WITCH": dict(
        label="Witch", description="Witch purple with lime sparkle dots",
        base="#8E5CFF", tint="#5A3AB0", highlight="#C8FF6A", hatch="#24104A",
        rim="#B6FF5A", line="#12061F", bg="#1E1430",
        settings={"Rim Amount": 0.7},
    ),
}

ORDER = ["SAKURA", "LEMON", "MINT", "SODA", "GRAPE", "PEACH", "MELON", "COMIC", "NEON_NIGHT", "CHOCO",
         "PUMPKIN", "GHOST", "WITCH"]


def hex_to_srgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb_to_linear_channel(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb_channel(c):
    c = max(0.0, c)
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def hex_to_linear(h, alpha=1.0):
    return tuple(srgb_to_linear_channel(c) for c in hex_to_srgb(h)) + (alpha,)


def linear_to_srgb(color):
    return tuple(linear_to_srgb_channel(c) for c in color[:3])
