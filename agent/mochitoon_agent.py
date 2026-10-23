"""MochiToon in one command. Written for AI agents; humans just ask their agent.

Install (once, permanent):
  blender -b --python mochitoon_agent.py -- --install mochitoon-x.y.z.zip
  (never add --factory-startup here: the install is saved into the user's preferences)

Make a .blend cute (installs first if --install is given and it is missing):
  blender -b scene.blend --python mochitoon_agent.py -- --palette SAKURA --shape HEART \
      --setup-scene --save scene_cute.blend --render preview.png

Options:
  --install ZIP         install + enable the extension from a zip (saved to user preferences)
  --palette NAME        SAKURA LEMON MINT SODA GRAPE PEACH MELON COMIC NEON_NIGHT CHOCO PUMPKIN GHOST WITCH
                        (omit to keep the scene's current palette; SAKURA for objects not yet MochiToon)
  --shape A+B           any mix of CIRCLE HEART STAR FLOWER SPARKLE MOON (e.g. STAR+FLOWER)
  --style NAME          GRID (classic halftone) or SPRINKLE (scattered stickers)
  --amount X            sticker amount: FEW SOME MANY LOTS or 0-1 (implies SPRINKLE)
  --light-rim X         white rim on the lit side, 0-1
  --glow X              bloom on the rim and shapes, 0-1
  --objects A,B         only these objects (default: every mesh in the scene)
  --keep-colors yes|no  keep each object's own color/texture (default: auto)
  --no-outline          skip the outline
  --setup-scene         EEVEE, Standard colors, crisp sun, flat background
  --smooth              subdivide low-poly rounded meshes (e.g. Suzanne); boxy meshes are skipped
  --frame-camera        point a MochiToon camera at all meshes (keeps the user's own camera untouched)
  --preview-size PCT    render size in % of the scene resolution, e.g. 50 for quick variation previews
  --save PATH           save the .blend here (default: do not save)
  --render PATH         render a PNG preview (adds a camera if the scene has none)
  --list                print the palettes and exit
Exit code 0 on success; the last line printed starts with "MOCHITOON OK" or "MOCHITOON ERROR".
"""

import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None, flag=False):
    if name not in argv:
        return default
    if flag:
        return True
    i = argv.index(name)
    return argv[i + 1] if i + 1 < len(argv) else default


def fail(msg):
    print("MOCHITOON ERROR", msg)
    sys.exit(1)


def installed():
    # bpy.ops.<anything> always exists, so ask for the registered operator class instead
    return hasattr(bpy.types, "MOCHITOON_OT_make_cute")


def install(zip_path):
    zip_path = os.path.abspath(zip_path)
    if not os.path.isfile(zip_path):
        fail(f"zip not found: {zip_path}")
    if bpy.app.factory_startup:
        fail("do not use --factory-startup when installing; it would overwrite the user's preferences")
    bpy.ops.extensions.package_install_files(filepath=zip_path, repo="user_default", enable_on_install=True)
    if not installed():
        # in background mode the freshly installed package is not enabled for this session yet
        import addon_utils
        addon_utils.enable("bl_ext.user_default.mochitoon", default_set=True, persistent=True)
    bpy.ops.wm.save_userpref()
    if not installed():
        fail("install finished but the add-on did not load")
    print("MochiToon installed:", zip_path)


def api_module():
    import importlib
    # e.g. "bl_ext.user_default.mochitoon.ops" -> "bl_ext.user_default.mochitoon.api"
    package = bpy.types.MOCHITOON_OT_make_cute.__module__.rsplit(".", 1)[0]
    return importlib.import_module(package + ".api")


def frame_camera(scene, objects):
    """A dedicated camera that sees every mesh; the user's own camera is left as it is."""
    cam = scene.objects.get("MochiToon Camera")
    if cam is None:
        cam = bpy.data.objects.new("MochiToon Camera", bpy.data.cameras.new("MochiToon Camera"))
        scene.collection.objects.link(cam)
    scene.camera = cam
    _aim(cam, objects)


def _aim(cam, objects):
    pts = [ob.matrix_world @ Vector(c) for ob in objects for c in ob.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    center, size = (lo + hi) / 2, max((hi - lo).length, 0.1)
    cam.data.lens = 50
    cam.location = center + Vector((0.0, -1.0, 0.3)).normalized() * size * 1.7
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()


def ensure_camera(scene, objects):
    if scene.camera is not None:
        return
    cam = bpy.data.objects.new("MochiToon Camera", bpy.data.cameras.new("MochiToon Camera"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    _aim(cam, objects)


def main():
    zip_path = arg("--install")
    if zip_path and not installed():
        install(zip_path)
    elif zip_path:
        print("MochiToon already installed")
    if not installed():
        fail("MochiToon is not installed (run with --install mochitoon.zip)")
    api = api_module()

    if arg("--list", flag=True):
        for key, label, desc in api.list_palettes():
            print(f"{key:12s} {label:12s} {desc}")
        print("MOCHITOON OK listed palettes")
        return

    has_job = any(a in argv for a in ("--palette", "--shape", "--style", "--amount", "--light-rim", "--glow",
                                      "--setup-scene", "--save", "--render", "--objects", "--smooth"))
    if not has_job:
        print("MOCHITOON OK", "installed" if zip_path else "nothing to do")
        return

    scene = bpy.context.scene
    names = arg("--objects")
    objs = api.resolve_objects("ALL", names=names.split(",") if names else None)
    keep = {"yes": True, "no": False}.get((arg("--keep-colors") or "").lower())
    try:
        num = lambda name: float(arg(name)) if arg(name) is not None else None  # noqa: E731
        amount = arg("--amount")
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            pass
        report = api.make_cute(objects=objs, palette=arg("--palette"), shape=arg("--shape"), smooth=arg("--smooth", flag=True),
                               keep_colors=keep, outline=not arg("--no-outline", flag=True),
                               setup_scene=arg("--setup-scene", flag=True), style=arg("--style"),
                               amount=amount, light_rim=num("--light-rim"), glow=num("--glow"))
    except ValueError as err:
        fail(str(err))
    print(report)

    render = arg("--render")
    if arg("--frame-camera", flag=True):
        frame_camera(scene, objs)
    if render:
        ensure_camera(scene, objs)
        if arg("--preview-size"):
            scene.render.resolution_percentage = int(float(arg("--preview-size")))
        scene.render.filepath = os.path.abspath(render)
        bpy.ops.render.render(write_still=True)
        print("preview:", scene.render.filepath)
    save = arg("--save")
    if save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save))
        print("saved:", os.path.abspath(save))
    print("MOCHITOON OK", report)


main()
