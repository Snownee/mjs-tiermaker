# mjs 输入图更新 → 数据更新流程

当 `slicer_mjs/input/` 里的卡池截图被**新增或替换**时，按本流程把头像与元数据同步进 `src_mjs/`，再进版本。

## 为什么分阶段

`slicer.py` 拆成 `slice` / `apply` / `data` 三段。它原先是一条龙：每次运行都**全量重建** `src_mjs/assets`，会把 `enhance.py` 的超分结果冲掉，导致迭代 OCR 时无法插入超分。分阶段后超分固定落在 `apply` 之后。

## 前置约定

- 输入图放 `slicer_mjs/input/`，**按朝代命名**（`秦.png`、`西汉2.png`…）。程序取文件名去掉数字作为朝代，决定 `name` 前缀与 `assets/<朝代>/` 目录名。
- 命令在 `slicer_mjs/` 目录下执行（脚本会自行 `chdir`）。
- 依赖在 root `.venv`。

## 步骤

### 1. 切片 —— `python slicer.py slice`
- OCR 切图 → `temp_output/<朝代>/<名字>.webp`，**不写** `src_mjs/`。
- 有误读：把错字加进 `NAME_MAPPING`（键 = 正确名，值 = 误读列表），重跑 `slice`。可反复运行，无副作用。
- 完成判据：`temp_output/` 下所有文件名都是正确角色名。

### 2. 校对卡包（多数在写库时自动完成）
- `pack` 由 `DYNASTY_PACK` 按朝代前缀自动补。
- 横跨多卡包的朝代（`MULTI_PACK_DYNASTIES`）在写库时打印警告，需人工决定该角色归哪个包。
- 整个朝代归属变了 → 改 `DYNASTY_PACK`；只是个别角色 → 先按第 3 步落库，再改 `id.json`，跑第 4 步。

### 3. 落库 —— `python slicer.py apply`
- 先把新条目追加进 `id.json`（含自动 `pack`），**只替换 `temp_output/` 里出现的朝代目录**，其余目录（含已超分的）原样保留。
- 同时重写 `data.js`。y/n 确认后生效。
- 完成判据：`src_mjs/assets/<朝代>/` 与 `temp_output/<朝代>/` 一致；`id.json` 新条目及其 `pack` 正确。

### 4. 同步 data.js（仅手动改过 `id.json` 时）—— `python slicer.py data`
- 由 `id.json` 重生成 `src_mjs/data.js`。没改 `id.json` 就不需要。

### 5. 超分 —— `python enhance/enhance.py`
- 原地 4x 超分 `src_mjs/assets`；增量——只处理哈希变化的新图，已超分的跳过。
- **必须紧跟在 `apply` 之后、build 之前。** 超分后不要再跑 `apply`/`all`，否则该朝代目录会被重新切片覆盖。
- 先 `python enhance/enhance.py --dry-run` 看将处理哪些。

### 6. 同步与构建 —— `npm run set_mjs` → `npm run build`（或 `npm run dev` 预览）

## 速查

| 目的 | 命令 |
|---|---|
| 切图 | `python slicer.py slice` |
| 落库（assets + id.json + data.js） | `python slicer.py apply` |
| 仅重生成 data.js | `python slicer.py data` |
| slice + apply 连跑 | `python slicer.py all` |
| 超分（先看） | `python enhance/enhance.py --dry-run` |
| 超分 | `python enhance/enhance.py` |

## 坑

- 别在 `enhance.py` 之后再跑 `slicer.py apply` / `all`，否则超分被覆盖（历史上正是这样丢过一次）。
- 输入图命名 = 朝代；文件名里的数字会被丢弃（`西汉.png` 与 `西汉2.png` 都归到 `西汉`）。
- WebP 编码是确定性的：输入像素不变时切片输出字节一致。所以「只改了两张图，其他朝代输出却也变了」通常意味着旧文件不是本切片的产物（例如被超分过）。
