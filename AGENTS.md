# AGENTS.md

## Data-source variants (critical)

- `src/data.js` and `src/assets/` are copied/generated, NOT sources of truth. Per-variant sources live in `src_mjs/`, `src_ark/`, `src_rocom/`, `src_ww/`, `src_v/` (v = vanilla/empty, used for GitHub Pages).
- `npm run set_<variant>` (runs `node set.js`) deletes `src/assets` then copies that variant's files into `src/`. Run it before `dev`/`build`; switching dirties the working tree (`src/data.js` is tracked, `src/assets/*/*.webp` is gitignored).
- `src/data_v.js` is NOT part of the copy mechanism — it is the vanilla variant imported directly by `src/App.vue`.
- `data.js` exports `namespace`, `data`, `presets`, `uiSettings`, `lang`. The `data` block sits between `/* DATA_START */` and `/* DATA_END */` markers; the Python slicers rewrite only this region.
- Character `name` strings use the `"faction/name"` format; `useCharacters.js` splits on the first `/`. Keep that invariant.

## Commands

- `npm run set_mjs | set_ark | set_rocom | set_ww | set_vanilla` — switch data source (sticky repo state).
- `npm run dev` / `npm run build` / `npm run preview`
- `npm run lint` — lints `src/` only, not the `src_*` folders.
- `local_build.ps1` — build, then zip `dist/` into `dist.zip`.
- `npm run bump | bump:minor` — npm version + push with tags; a `v*` tag triggers the release workflow.
- No test framework. `test.html` is a gitignored manual dev page.

## CI/CD

- Push to `main` → GitHub Actions builds the **vanilla** variant (`set_vanilla`) with `MJS_TIERMAKER_BASE_URL=/mjs-tiermaker/` and deploys `dist/` to `gh-pages`. It switches the variant itself, so the state of `src/` on main doesn't matter.
- `v*` tag → release.yml builds all 5 variants and publishes `release-build-<variant>.zip` to releases named `{tag}+{variant}`.
- `MJS_TIERMAKER_BASE_URL` env sets Vite `base` (default `./`).

## Save/share format (`src/save.js`)

- URL-shared tier lists: `0` version prefix + pako-deflated big-endian byte stream (null-terminated strings, item IDs as unsigned shorts, max 65535, tierCount `0` means default tiers). Changing the format requires bumping the version prefix and keeping `load()` backward-compatible.

## Python slicers (`slicer_<variant>/`)

- One standalone script per variant; each hardcodes its target as `../src_<variant>/` (data.js + assets). Don't copy one slicer into another without updating those paths.
- When you add or replace a卡池截图 in `slicer_mjs/input/`, follow the runbook `slicer_mjs/WORKFLOW.md` (slice → 校对 → apply → enhance → set_mjs). mjs `slicer.py` is three stages: `slice` (OCR → `temp_output/`, writes nothing else), `apply` (writes `assets/` — replacing **only the 朝代 dirs present in `temp_output/`** — plus `id.json` and `data.js`), `data` (regenerate `data.js` from `id.json`). `apply` auto-fills each new entry's `pack` from `DYNASTY_PACK` by 朝代前缀. The other variants still run as a single `slicer.py` pass.
- ww/rocom slicers merge card metadata from `data_export.json`, produced by the Tampermonkey `export.user.js` scripts.
- Python deps are in root `requirements.txt`, installed in root `.venv`. Scripts use `np.fromfile` + `cv2.imdecode` to survive non-ASCII Windows paths.
- OCR mistakes are corrected via per-script `NAME_MAPPING` dicts — add new misreads there, not in `data.js`.

## Webp 超分增强 (`enhance/`)

- `enhance/enhance.py` 用 Real-ESRGAN (realesrgan-ncnn-vulkan) 对 webp 资产做 4x 超分，原地覆盖，提升清晰度。引擎二进制在 `enhance/engine/`（gitignore，首次运行自动下载）。
- 逐目录独立参数写在 `enhance/config.json` 的 `targets`（每项含 `path`、`model`、`webp_q`）。当前只配了 `../src_mjs/assets`。
- 去重靠 `enhance/processed.json`（入库）：每条 = 图片相对路径 → `{input_sha256, output_sha256, params, time}`。跳过条件 = 当前文件哈希 == `output_sha256` 且 `params`（含引擎哈希）未变；否则重处理并更新输入/输出哈希。
- 用法：`python enhance/enhance.py --dry-run`（只列将处理项）、`python enhance/enhance.py`（执行）、`python enhance/enhance.py --pilot N --models m1 m2`（抽 N 张双模型对照到 `enhance/_pilot/`，不写目标目录）。
- 生成改动资产时记得 `npm run set_<variant>` 同步到 `src/` 并跑 `npm run build` 回归。

## Stack notes

- Vue 3 + Vite 8 (rolldown) + Element Plus (zh-cn locale, dark default). No TypeScript; `@` aliases to `src/` (jsconfig.json).
- UI copy is Chinese; keep new UI text consistent.
- Global `__BUILD_TIME__` (YYYY-MM-DD, Asia/Shanghai) is injected by vite.config.js and declared in `.eslintrc.json` globals.

## 重要：用户特别指定的规则

1. 编写代码时，不要进行冗余的防御性检查（如null检查），而应让程序尽早失败，以便快速发现问题。
2. 使用中文进行回复。