import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

import cv2
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(SCRIPT_DIR, "engine")
ENGINE_EXE = os.path.join(ENGINE_DIR, "realesrgan-ncnn-vulkan.exe")
ENGINE_MODELS_DIR = os.path.join(ENGINE_DIR, "models")
ENGINE_URL = (
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/"
    "realesrgan-ncnn-vulkan-20220424-windows.zip"
)
RECORD_PATH = os.path.join(SCRIPT_DIR, "processed.json")
WORK_DIR = os.path.join(SCRIPT_DIR, "_work")
PILOT_DIR = os.path.join(SCRIPT_DIR, "_pilot")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

BATCH = 40
STAGE_IN = os.path.join(WORK_DIR, "in")
STAGE_OUT = os.path.join(WORK_DIR, "out")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(open(path, "rb").read())


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def resolve(path):
    if not os.path.isabs(path):
        path = os.path.join(SCRIPT_DIR, path)
    return os.path.normpath(path)


def rel_key(path):
    return os.path.relpath(path, SCRIPT_DIR).replace("\\", "/")


def ensure_engine():
    if os.path.isfile(ENGINE_EXE) and os.path.isdir(ENGINE_MODELS_DIR):
        return
    os.makedirs(WORK_DIR, exist_ok=True)
    zip_path = os.path.join(WORK_DIR, "realesrgan-ncnn-vulkan.zip")
    print(f"下载引擎 {ENGINE_URL}")
    req = urllib.request.Request(ENGINE_URL, headers={"User-Agent": "enhance.py"})
    with urllib.request.urlopen(req) as resp, open(zip_path, "wb") as out:
        total = int(resp.headers.get("Content-Length", 0))
        done = 0
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r下载进度 {done / total:.1%}", end="", flush=True)
    print()
    os.makedirs(ENGINE_DIR, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for entry in z.infolist():
            name = entry.filename
            if name in ("input.jpg", "input2.jpg", "onepiece_demo.mp4", "README_windows.md"):
                continue
            if "/" in name and not name.startswith("models/"):
                continue
            target = os.path.join(ENGINE_DIR, name)
            parent = os.path.dirname(target)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with z.open(entry) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
    print(f"引擎就绪: {ENGINE_DIR}")
    if not (os.path.isfile(ENGINE_EXE) and os.path.isdir(ENGINE_MODELS_DIR)):
        raise RuntimeError("引擎下载后仍不完整")


def list_webp(target_dir):
    result = []
    for root, _dirs, files in os.walk(target_dir):
        for name in sorted(files):
            if name.lower().endswith(".webp"):
                result.append(os.path.join(root, name))
    return result


def engine_id():
    return sha256_file(ENGINE_EXE)[:12]


def engine_cmd(in_path, out_path, model, scale):
    return [
        ENGINE_EXE,
        "-i", in_path,
        "-o", out_path,
        "-s", str(scale),
        "-m", ENGINE_MODELS_DIR,
        "-n", model,
        "-f", "png",
    ]


def decode_bytes(data):
    return cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)


def encode_webp(img, quality):
    ok, buf = cv2.imencode(".webp", img, [int(cv2.IMWRITE_WEBP_QUALITY), quality])
    if not ok:
        raise RuntimeError("webp 编码失败")
    return buf.tobytes()


def upscale_png_bytes(png_bytes, model, scale):
    os.makedirs(WORK_DIR, exist_ok=True)
    in_path = os.path.join(WORK_DIR, "single_in.png")
    out_path = os.path.join(WORK_DIR, "single_out.png")
    if os.path.exists(out_path):
        os.remove(out_path)
    with open(in_path, "wb") as f:
        f.write(png_bytes)
    proc = subprocess.run(engine_cmd(in_path, out_path, model, scale), capture_output=True)
    if proc.returncode != 0 or not os.path.exists(out_path):
        tail = proc.stderr.decode("utf-8", errors="replace").strip().splitlines()
        raise RuntimeError(f"引擎失败 ({model}): {tail[-3:] if tail else '无输出'}")
    with open(out_path, "rb") as f:
        return f.read()


def reset_staging():
    for d in (STAGE_IN, STAGE_OUT):
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)


def process_pending(pending, params):
    results = {}
    errors = []
    reset_staging()
    order = []
    for i, path in enumerate(sorted(pending)):
        raw = open(path, "rb").read()
        img = decode_bytes(raw)
        if img is None:
            errors.append((path, "解码失败"))
            continue
        ok, png = cv2.imencode(".png", img)
        if not ok:
            errors.append((path, "png 暂存编码失败"))
            continue
        with open(os.path.join(STAGE_IN, f"{i:05d}.png"), "wb") as f:
            f.write(png.tobytes())
        order.append((i, path, raw))
    proc = subprocess.run(
        engine_cmd(STAGE_IN, STAGE_OUT, params["model"], params["scale"]),
        capture_output=True,
    )
    if proc.returncode != 0:
        tail = proc.stderr.decode("utf-8", errors="replace").strip().splitlines()
        raise RuntimeError(f"引擎批量失败 ({params['model']}): {tail[-5:] if tail else '无输出'}")
    for i, path, raw in order:
        stage = os.path.join(STAGE_OUT, f"{i:05d}.png")
        try:
            if not os.path.exists(stage):
                raise RuntimeError("引擎未产出该文件")
            up_img = decode_bytes(open(stage, "rb").read())
            if up_img is None:
                raise RuntimeError("引擎输出解码失败")
            results[path] = (raw, encode_webp(up_img, params["webp_q"]))
        except Exception as exc:
            try:
                ok, png = cv2.imencode(".png", decode_bytes(raw))
                up_png = upscale_png_bytes(png.tobytes(), params["model"], params["scale"])
                results[path] = (raw, encode_webp(decode_bytes(up_png), params["webp_q"]))
            except Exception as exc2:
                errors.append((path, f"{exc} / 单张重试也失败: {exc2}"))
    return results, errors


def process_and_record(pending, params, record):
    results, errors = process_pending(pending, params)
    for path, (input_raw, output_bytes) in results.items():
        record[rel_key(path)] = {
            "input_sha256": sha256_bytes(input_raw),
            "output_sha256": sha256_bytes(output_bytes),
            "params": params,
            "time": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        with open(path, "wb") as f:
            f.write(output_bytes)
        print(f"  [已处理] {rel_key(path)}")
    return errors


def run_targets(dry_run):
    config = load_json(CONFIG_PATH, {"targets": []})
    record = load_json(RECORD_PATH, {})
    if not (os.path.isfile(ENGINE_EXE) and os.path.isdir(ENGINE_MODELS_DIR)):
        if dry_run:
            print("引擎未安装（dry-run 不下载）")
            return 1
        ensure_engine()
    eid = engine_id()
    errors = []
    skipped = processed = 0
    for target in config["targets"]:
        target_dir = resolve(target["path"])
        params = {
            "model": target.get("model", "realesrgan-x4plus"),
            "scale": int(target.get("scale", 4)),
            "webp_q": int(target.get("webp_q", 100)),
            "engine": eid,
        }
        pending = []
        skip_here = 0
        for img_path in list_webp(target_dir):
            key = rel_key(img_path)
            entry = record.get(key)
            if entry and entry.get("output_sha256") == sha256_file(img_path) and entry.get("params") == params:
                skip_here += 1
            else:
                pending.append(img_path)
        skipped += skip_here
        print(f"目录 {target_dir}: 待处理 {len(pending)}, 跳过 {skip_here}")
        if dry_run:
            for p in pending:
                print(f"  [将处理] {rel_key(p)}")
            processed += len(pending)
            continue
        for start in range(0, len(pending), BATCH):
            chunk = pending[start:start + BATCH]
            print(f"  批次 {start // BATCH + 1}/{(len(pending) - 1) // BATCH + 1} ({len(chunk)} 张)")
            errors.extend(process_and_record(chunk, params, record))
            processed += len(chunk)
        save_json(RECORD_PATH, record)
    print(f"\n完成: 处理 {processed}, 跳过 {skipped}, 失败 {len(errors)}")
    for key, msg in errors:
        print(f"  失败 {key}: {msg}")
    return 1 if errors else 0


def pick_samples(n):
    by_dir = {}
    config = load_json(CONFIG_PATH, {"targets": []})
    for target in config["targets"]:
        for f in list_webp(resolve(target["path"])):
            by_dir.setdefault(os.path.dirname(f), []).append(f)
    dirs = sorted(by_dir)
    samples = []
    idx = 0
    while len(samples) < n and by_dir:
        for d in dirs:
            if idx < len(by_dir[d]):
                samples.append(by_dir[d][idx])
                if len(samples) == n:
                    break
        idx += 1
    return samples


def draw_label(img, text):
    h, w = img.shape[:2]
    canvas = np.full((30 + h + 6, w, 3), 40, dtype=np.uint8)
    cv2.putText(canvas, text, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (240, 240, 240), 2, cv2.LINE_AA)
    canvas[30 + 3:30 + 3 + h, :] = img
    return canvas


def run_pilot(n, models):
    if not (os.path.isfile(ENGINE_EXE) and os.path.isdir(ENGINE_MODELS_DIR)):
        ensure_engine()
    samples = pick_samples(n)
    if not samples:
        print("没有可用的样本")
        return 1
    tags = {"baseline": "original x4 (lanczos4 baseline)"}
    for m in models:
        tags[m] = m
    count = 0
    for img_path in samples:
        img = decode_bytes(open(img_path, "rb").read())
        h, w = img.shape[:2]
        baseline = cv2.resize(img, (w * 4, h * 4), interpolation=cv2.INTER_LANCZOS4)
        panels = {"baseline": baseline}
        for m in models:
            ok, png = cv2.imencode(".png", img)
            if not ok:
                raise RuntimeError("png 暂存编码失败")
            panels[m] = decode_bytes(upscale_png_bytes(png.tobytes(), m, 4))
        rel = os.path.splitext(os.path.relpath(img_path, os.path.dirname(SCRIPT_DIR)))[0]
        out_dir = os.path.join(PILOT_DIR, os.path.dirname(rel))
        os.makedirs(out_dir, exist_ok=True)
        sheet = None
        for tag in tags:
            panel = draw_label(panels[tag], tags[tag])
            sheet = panel if sheet is None else np.hstack([sheet, panel])
        ok, buf = cv2.imencode(".png", sheet)
        if not ok:
            raise RuntimeError("sheet 编码失败")
        sheet_path = os.path.join(out_dir, os.path.basename(rel) + "_对比.png")
        with open(sheet_path, "wb") as f:
            f.write(buf)
        count += 1
        print(f"[{count}/{len(samples)}] {sheet_path}")
    print(f"对照图已生成: {PILOT_DIR}")
    return 0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Real-ESRGAN webp 清晰度提升")
    parser.add_argument("--pilot", type=int, metavar="N", help="抽 N 张样本跑模型对照，不写目标目录")
    parser.add_argument(
        "--models", nargs="+", default=["realesrgan-x4plus", "realesrgan-x4plus-anime"],
        help="对照模型（默认 x4plus 与 x4plus-anime）",
    )
    parser.add_argument("--dry-run", action="store_true", help="只列出将处理的文件，不写盘")
    args = parser.parse_args()
    if args.pilot:
        return run_pilot(args.pilot, args.models)
    return run_targets(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
