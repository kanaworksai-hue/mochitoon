# SPDX-FileCopyrightText: 2026 東京AI映像合同会社 (Tokyo AI Visuals LLC)
# SPDX-License-Identifier: GPL-3.0-or-later
"""MochiToon: cute comic-style toon shading for EEVEE in one click."""

import bpy

from . import nodes, ops, ui


@bpy.app.handlers.persistent
def _upgrade_on_load(_dummy):
    # files saved with an older MochiToon get the new shader (values kept) as soon as they open
    if bpy.data.node_groups.get(nodes.GROUP_NAME) is not None:
        nodes.ensure_group()


def register():
    ops.register()
    ui.register()
    bpy.app.handlers.load_post.append(_upgrade_on_load)


def unregister():
    if _upgrade_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_upgrade_on_load)
    ui.unregister()
    ops.unregister()
