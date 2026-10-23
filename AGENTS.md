# MochiToon — instructions for AI agents

The human only says something like *"make my Blender scene cute / manga style"* or
*「MochiToonでかわいくして」*. You do everything: install, apply, show a preview.
Do not ask the human to click anything in Blender.

## 1. Find Blender
- macOS: `/Applications/Blender*.app/Contents/MacOS/Blender` (pick the newest, needs 4.2+)
- Windows: `C:\Program Files\Blender Foundation\Blender */blender.exe`
- Linux: `blender` on PATH
Check with `<blender> --version`.

## 2. Install (once)
Get the latest `mochitoon-<version>.zip` from https://github.com/kanaworksai-hue/mochitoon/releases
(`gh release download -R kanaworksai-hue/mochitoon -p 'mochitoon-*.zip'`), and `agent/mochitoon_agent.py`
from the repository, then:

```bash
<blender> -b --python agent/mochitoon_agent.py -- --install mochitoon-<version>.zip
```

Never add `--factory-startup` to the install command — the install is saved into the user's
preferences and factory startup would overwrite them. The script refuses in that case.
Success = last line starts with `MOCHITOON OK`.

## 3. Apply

### a) To a .blend file (Blender closed, headless)
```bash
<blender> -b scene.blend --python agent/mochitoon_agent.py -- \
    --palette SAKURA --shape HEART --setup-scene \
    --save scene_cute.blend --render preview.png
```
Install and apply can be one command: add `--install mochitoon-<version>.zip`.
Show the human `preview.png`. Save to a new file unless they asked to overwrite.

### b) Into a running Blender (e.g. through a Blender MCP / Python console)
```python
import bpy
bpy.ops.mochitoon.make_cute(palette="SAKURA", shape="HEART", target="SELECTED_OR_ALL", setup_scene=True)
bpy.ops.mochitoon.make_cute(palette="PUMPKIN", shape="STAR+MOON+SPARKLE", amount="FEW", light_rim=0.8, glow=0.5)
```
`target`: `SELECTED_OR_ALL` (default), `SELECTED`, `ALL`.
`keep_colors`: `AUTO` (default: textured models keep their textures), `YES`, `NO`.
`outline`: `True`/`False`.

## 4. Turning the human's words into options

| They say | palette |
|---|---|
| pink, sakura, 桜, ピンク, 粉色, 樱花 | `SAKURA` |
| yellow, lemon, 黄色, レモン, 柠檬 | `LEMON` |
| mint, green, ミント, 薄荷 | `MINT` |
| sky blue, soda, 水色, ソーダ, 苏打 | `SODA` |
| purple, lavender, grape, 紫, ぶどう, 葡萄 | `GRAPE` |
| peach, orange pastel, ピーチ, 桃, 蜜桃 | `PEACH` |
| lime, melon, メロン, 蜜瓜 | `MELON` |
| classic comic, red, アメコミ, 漫画红 | `COMIC` |
| black, neon, cyber, night, 黒猫, ネオン, 霓虹 | `NEON_NIGHT` |
| brown, chocolate, チョコ, 巧克力 | `CHOCO` |
| halloween, pumpkin, ハロウィン, かぼちゃ, 南瓜 | `PUMPKIN` |
| ghost, white spooky, おばけ, 幽灵 | `GHOST` |
| witch, magic, 魔女, 巫师 | `WITCH` |

| They say | shape (mix freely with `+`) |
|---|---|
| dots, 網点, 圆点 (default) | `CIRCLE` |
| hearts, ハート, 爱心 | `HEART` |
| stars, 星, 星星 | `STAR` |
| flowers, 花, 小花 | `FLOWER` |
| sparkle, twinkle, キラキラ, 闪光 | `SPARKLE` |
| moon, 月, 月亮 | `MOON` |

| They say | option |
|---|---|
| classic comic dots, 網点, 网点 | `--style GRID` |
| scattered, stickers, ちらし, 散らして, 散开 | `--style SPRINKLE` |
| fewer / just a few / 少なめ / 少一点 | `--amount FEW` |
| more / たくさん / 多一点 | `--amount MANY` |
| shiny edge, rim light, 縁が光る, 边缘光 | `--light-rim 0.8` |
| glowy, glow, 光らせて, 发光 | `--glow 0.5` |

"Keep my colors / textures" → `--keep-colors yes`. "No outline" → `--no-outline`.
Too busy / "密集恐怖症" / "too many hearts" → `--style SPRINKLE --amount FEW`.
Unknown palette names fail with a list of valid ones; pick the closest and tell the human.

## 5. Fine-tuning after applying (running Blender)
The material has a node group "MochiToon Core". Useful inputs on that group node:
`Shadow Threshold` (0–1, more = bigger shadow), `Highlight Size` (0–1), `Dot Density` (dots per screen),
`Hatch Amount` (0–1), `Rim Amount` (0–1), `Shadow Tint` (color multiplied into the shadow).
```python
from bpy import data
mat = data.objects["Cube"].active_material
core = next(n for n in mat.node_tree.nodes if n.type == "GROUP" and n.node_tree.name.startswith("MochiToon Core"))
core.inputs["Highlight Size"].default_value = 0.8
```

## Getting the best result (do this, the human won't ask)
1. Render a preview (`--render preview.png`) and look at it before reporting back.
2. Busy-looking? Switch to `SPRINKLE` with `FEW`; flat-looking? add `--light-rim 0.8 --glow 0.4`.
3. Textured models (scans, generated characters) keep their textures automatically; plain models take the palette color.
4. Offer two or three variations (palette × shapes) as small previews and let the human pick in one word.
5. Report what you changed in one sentence, with the preview.

## Notes
- Needs EEVEE. `--setup-scene` / `setup_scene=True` switches to EEVEE, Standard view transform, a sun and a flat background.
- Orthographic cameras are not supported yet.
