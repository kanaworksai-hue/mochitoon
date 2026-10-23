# MochiToon

![MochiToon — AIに一言で、3Dがマンガ風に！](docs/hero.jpg)

**AIに一言で、3Dがかわいいマンガ風に。**
**Cute comic toon shading for Blender, in one sentence to your AI.**
**对 AI 说一句话，3D 就变成可爱的漫画风。**

無料・オープンソース（GPL-3.0-or-later）／ Free and open source ／ 免费开源 — Blender 4.2+, EEVEE

[日本語](#日本語) · [English](#english) · [中文](#中文)

## AIに頼むだけ ｜ Just ask your AI agent ｜ 交给 AI 就行

自分でインストールする必要はありません。AIエージェントにこう送るだけ：

> https://github.com/kanaworksai-hue/mochitoon の AGENTS.md に従って MochiToon をインストールして、私の Blender シーンをかわいいマンガ風にして。

You don't install anything yourself. Send this to your AI agent:

> Install MochiToon from https://github.com/kanaworksai-hue/mochitoon (follow its AGENTS.md) and make my Blender scene look like a cute comic.

不用自己安装，把这句话发给你的 AI 助手：

> 按照 https://github.com/kanaworksai-hue/mochitoon 的 AGENTS.md 安装 MochiToon，然后把我的 Blender 场景变成可爱的漫画风。

AIは [AGENTS.md](AGENTS.md) を読んで、インストール・適用・プレビューまで自動で行います。
The agent reads [AGENTS.md](AGENTS.md), installs the add-on, applies it and shows you a preview.
AI 会读取 [AGENTS.md](AGENTS.md)，自动完成安装、应用和预览。

## ギャラリー ｜ Gallery ｜ 效果一览

### 5つの層 ｜ Five layers ｜ 五层叠加

![Plain 3D → colored shadow → stickers → hatching → light rim → outline](docs/layers.png)

### ハイライトの形 ｜ Highlight shapes ｜ 高光图形

6種類を自由に組み合わせ ／ Mix any of the six ／ 六种图形自由搭配

![Circle, heart, star, flower, sparkle, moon](docs/shapes.png)

### 網点とちらし ｜ Halftone or stickers ｜ 网点与散布贴纸

![Halftone grid vs sprinkle stickers](docs/styles.png)

### 光の向きで変わる ｜ Reacts to the light ｜ 随光线变化

![Front light, side light, back light](docs/lighting.png)

### パレット13種 ｜ 13 palettes ｜ 13 套配色

![13 palettes](docs/palettes.png)

### Blender のパネル ｜ The panel ｜ 面板

手動で使うときは 3Dビューで **N** → **MochiToon** タブ ／ For manual use: **N** in the 3D Viewport → **MochiToon** tab ／ 手动使用：3D 视图按 **N** → **MochiToon** 标签页

![MochiToon panel in Blender](docs/panel.png)

---

## 日本語

MochiToon は、どんなオブジェクトもマンガ印刷風にします：

- **色つきの影**：影に色が入る（ピンク→ラベンダー、黄→オレンジ）。灰色にくすまない
- **ハイライトの形**：マンガの網点、または **ちらし**（まばら・大きさと角度がランダム）
- **6種類を自由に組み合わせ**：**丸・ハート・星・小花・キラキラ・月**
- **縁の光＋グロー**：光が当たる側の輪郭が光る（逆光でキラッ）
- **斜線（ハッチング）**：影の中に入り、暗いところほど密になる
- **リムライト**：影側のふちに光が入る。黒猫やネオン風に
- **アウトライン**：太さはオブジェクトの大きさに合わせて自動調整。色はパレットに合わせ、真っ黒にしない
- **パレット13種**（プレビュー付き）：さくら、レモン、ミント、ソーダ、ぶどう、ピーチ、メロン、コミック、ネオン、チョコ、かぼちゃ、おばけ、魔女
- **元の色・テクスチャを保持**：オブジェクトの色はそのままで、影・網点・線だけパレットから取る
- **オブジェクトに固定**：動くオブジェクトでも網点が泳がない
- **かわいいシーン設定**：EEVEE、Standard 表示（AgX だとパステルが白っぽくなる）、くっきりした太陽光、単色の背景

### インストール
1. [Releases](https://github.com/kanaworksai-hue/mochitoon/releases) から `mochitoon-x.y.z.zip` をダウンロード
2. Blender → 編集 → プリファレンス → エクステンションを入手 → 右上の ▾ → **ディスクからインストール…** → zip を選択
3. 3Dビューで **N** キー → **MochiToon** タブ

### 使い方
1. オブジェクトを選択
2. パレットを選ぶ
3. **Make It Cute**
4. **Setup Cute Scene**（シーンごとに1回）
5. **Look** と **Outline** で微調整

---

## English

MochiToon turns any object into a printed-comic look:

- **Colored shadows**: shadows are tinted (pink → lilac, yellow → orange), never gray or muddy
- **Highlight shapes**: a classic halftone grid, or **scattered stickers** (fewer, random size and angle)
- **Six shapes, mix freely**: **circle, heart, star, flower, sparkle, moon**
- **Light rim with glow**: a bright edge on the lit side (back light makes it sparkle), with soft bloom
- **Hatching** inside the shadow that gets denser where it is darker
- **Rim light** on the shadow side (great for black cats and neon looks)
- **Outline** that scales with object size, with a palette color instead of plain black
- **13 palettes** with preview icons: Sakura, Lemon, Mint, Soda, Grape, Peach, Melon, Comic, Neon Night, Choco, Pumpkin, Ghost, Witch
- **Keep Object Colors / Textures**: keep each object's own color or texture and take only the shadow, shapes and lines from the palette
- **Stick to Object**: lock the dot pattern to a moving object so it doesn't "swim"
- **Setup Cute Scene**: EEVEE, Standard color view (AgX washes out candy colors), a crisp sun and a flat background

### Install
1. Download `mochitoon-x.y.z.zip` from [Releases](https://github.com/kanaworksai-hue/mochitoon/releases)
2. Blender → Edit → Preferences → Get Extensions → ▾ (top right) → **Install from Disk…** → pick the zip
3. 3D Viewport → press **N** → **MochiToon** tab

### Use
1. Select objects
2. Pick a palette
3. **Make It Cute**
4. **Setup Cute Scene** (once per scene)
5. Fine-tune in **Look** and **Outline**

### Tips
- The shadow threshold is tuned for the sun from *Setup Cute Scene* (strength π). With your own lights, adjust **Shadow → Size**.
- Shapes and hatching are in screen space, so they stay the same size on screen like real screentone. Turn **Density** up for smaller shapes in big renders.
- Orthographic cameras are not supported yet.

---

## 中文

MochiToon 能把任何物体变成漫画印刷风格：

- **彩色阴影**：阴影带颜色（粉→淡紫、黄→橙），不会发灰发脏
- **高光图形**：经典网点，或“散布贴纸”（稀疏、大小和角度随机）
- **六种图形，自由混搭**：**圆点、爱心、星星、小花、闪光、月亮**
- **受光边缘光 + 辉光**：受光一侧轮廓发亮，逆光时会“闪”一下
- **排线**：画在阴影里，越暗越密
- **边缘光**：在阴影一侧，适合黑猫、霓虹风
- **描边**：粗细随物体大小自动调整，颜色跟随配色，不是死黑
- **13 套配色**，带预览图：樱花、柠檬、薄荷、苏打、葡萄、蜜桃、蜜瓜、漫画、霓虹夜、巧克力、南瓜、幽灵、魔女
- **保留物体原色和贴图**：物体保留自己的颜色或贴图，只从配色里拿阴影、图形和线条
- **跟随物体**：网点固定在运动的物体上，不会“游动”
- **一键可爱场景**：切换到 EEVEE、色彩视图设为 Standard（AgX 会把糖果色洗淡）、设置清晰的太阳光和纯色背景

### 安装
1. 从 [Releases](https://github.com/kanaworksai-hue/mochitoon/releases) 下载 `mochitoon-x.y.z.zip`
2. Blender → 编辑 → 偏好设置 → 获取扩展 → 右上角 ▾ → **从磁盘安装…** → 选这个 zip
3. 在 3D 视图里按 **N** → 打开 **MochiToon** 标签页

### 使用
1. 选中物体
2. 选一套配色
3. 点 **Make It Cute**
4. 点 **Setup Cute Scene**（每个场景点一次）
5. 在 **Look** 和 **Outline** 里微调

---

## Development

```bash
# render test images to tests/out/
blender -b --factory-startup --python tests/render_demo.py -- "$PWD/tests/out/demo.png" SAKURA 1

# operator smoke test
blender -b --factory-startup --python tests/test_ops.py

# build the extension zip into dist/
blender --factory-startup --command extension build --source-dir mochitoon --output-dir dist
```

MochiToon by KanaWorks_AI — https://x.com/KanaWorks_AI
