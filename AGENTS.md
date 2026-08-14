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
- Workflow: drop atlas screenshots into `input/` → run `slicer.py` → OCR splits avatars into `assets/<pack>/<name>.webp`, updates `id.json` and the DATA_START/DATA_END region of `data.js` (prompts y/n before writing).
- ww/rocom slicers merge card metadata from `data_export.json`, produced by the Tampermonkey `export.user.js` scripts.
- Python deps are in root `requirements.txt`, installed in root `.venv`. Scripts use `np.fromfile` + `cv2.imdecode` to survive non-ASCII Windows paths.
- OCR mistakes are corrected via per-script `NAME_MAPPING` dicts — add new misreads there, not in `data.js`.

## Stack notes

- Vue 3 + Vite 8 (rolldown) + Element Plus (zh-cn locale, dark default). No TypeScript; `@` aliases to `src/` (jsconfig.json).
- UI copy is Chinese; keep new UI text consistent.
- Global `__BUILD_TIME__` (YYYY-MM-DD, Asia/Shanghai) is injected by vite.config.js and declared in `.eslintrc.json` globals.

## 重要：用户特别指定的规则

1. 编写代码时，不要进行冗余的防御性检查（如null检查），而应让程序尽早失败，以便快速发现问题。
2. 使用中文进行回复。