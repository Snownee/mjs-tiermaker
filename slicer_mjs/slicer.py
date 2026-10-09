import cv2
from cnocr import CnOcr
import argparse
import shutil
import os
import difflib
import numpy as np
import json

# 初始化轻量级 OCR
ocr = CnOcr(rec_model_name="doc-densenet_lite_136-gru")

# --- 名字纠错配置 ---
# 键为正确名字，值为 OCR 经常认错的结果列表
NAME_MAPPING = {
    "荀彧": ["荀或"],
    "张春华": ["张春化"],
    "张郃": ["张邰", "张鸽", "张邵", "张部"],
    "芈八子": ["业八子"],
    "申不害": ["中不害"],
    "平原君": ["乎原君"],
    "钟离眜": ["钟离昧", "钟离眛"],
    "陆逊": ["陆迅"],
    "袁绍": ["哀绍"],
    "袁术": ["哀术"],
    "貂蝉": ["貂蛐"],
    "侯嬴": ["侯赢"],
    "平阳公主": ["乎阳公主"],
    "陈平": ["陈乎"],
    "桑弘羊": ["桑弘兰"],
    "项梁": ["项粱"],
    "嬴政": ["赢政"],
    "范雎": ["范睢"],
    "曹丕": ["曹不"],
    "庞煖": ["庞媛"],
    "卫玠": ["卫坋", "卫瑜"],
    "王濬": ["王溶"],
    "司马相如": ["与马相如"],
    "金日磾": ["金日殚"],
    "金日磾": ["金日殚"],
    "左棻": ["左荣"],
    # 在这里继续添加你遇到的生僻字或错误识别对
}

# --- 朝代 -> 卡包 映射 ---
# 新增条目按 name 前缀（朝代/势力）自动补全 pack。
# 一个朝代横跨多个卡包时，这里取现有数据中出现次数最多的主卡包；
# 命中 MULTI_PACK_DYNASTIES 的朝代会在新增时打印警告，需人工核对。
DYNASTY_PACK = {
    "东汉": "三国云起",
    "孙吴": "三国云起",
    "曹魏": "三国云起",
    "蜀汉": "三国云起",
    "黄巾": "三国云起",
    "张楚": "楚汉之争",
    "西楚": "楚汉之争",
    "秦": "秦扫六合",
    "燕": "秦扫六合",
    "西汉": "汉武盛世",
    "楚": "合纵连横",
    "赵": "合纵连横",
    "韩": "合纵连横",
    "魏": "合纵连横",
    "齐": "合纵连横",
    "西晋": "晋洛兴替",
    "东晋": "王马天下",
    "西周": "匠心天工",
}

# 横跨多个卡包的朝代，自动补的主卡包可能不准，需人工确认
MULTI_PACK_DYNASTIES = {"秦", "燕", "西汉", "曹魏", "楚", "赵", "韩", "魏", "齐"}

INPUT_FOLDER = "input"
TEMP_FOLDER = "temp_output"
ID_FILE = "id.json"

TARGET_FILE = "../src_mjs/data.js"
DATA_START = "/* DATA_START */"
DATA_END = "/* DATA_END */"
DATA_TEMPLATE = "export const data = {0}"

TARGET_FOLDER = "../src_mjs/assets"


def write_to_target_file(new_data):
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    start_index = content.find(DATA_START)
    end_index = content.find(DATA_END)

    if start_index == -1 or end_index == -1:
        print("Error: DATA_START or DATA_END not found in target file.")
        return

    new_content = (
        content[: start_index + len(DATA_START)]
        + "\n"
        + DATA_TEMPLATE.format(json.dumps(new_data, indent=4, ensure_ascii=False))
        + "\n"
        + content[end_index:]
    )

    with open(TARGET_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Successfully updated {TARGET_FILE} with new data.")


def alias_fix(raw_name):
    """
    纠正 OCR 识别结果
    1. 精确匹配映射表
    2. 如果没匹配到，尝试计算相似度（防止出现一个错别字的情况）
    """
    raw_name = raw_name.strip()
    if not raw_name:
        return "Unknown"

    # 1. 直接检查映射表
    for correct_name, aliases in NAME_MAPPING.items():
        if raw_name == correct_name or raw_name in aliases:
            return correct_name

    # # 2. 模糊匹配：计算识别结果与所有正确名字的相似度
    # # 如果相似度高于 0.6，则认为是该角色
    # all_correct_names = list(NAME_MAPPING.keys())
    # matches = difflib.get_close_matches(raw_name, all_correct_names, n=1, cutoff=0.6)

    # if matches:
    #     return matches[0]

    return raw_name


def process_atlas(image_path, output_folder="output"):
    print(f"Processing: {image_path}")
    outputs = []

    # 获取路径中不含扩展名的文件名
    filename = os.path.splitext(os.path.basename(image_path))[0]
    # 删除filename中的数字
    filename = "".join(c for c in filename if not c.isdigit())
    output_folder = os.path.join(output_folder, filename)
    os.makedirs(output_folder, exist_ok=True)

    img_array = np.fromfile(image_path, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. 阈值处理，便于提取矩形轮廓
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    names = set()

    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)

        # 过滤掉非头像的小区域 (根据实际头像像素大小调整)
        if w > 40 and h > 40:
            # A. 裁剪头像本体
            avatar = img[y : y + h, x : x + w]

            # B. 裁剪名字区域 (假设名字在头像下方 5-35 像素位置)
            # 你可以根据实际图片的行间距微调这个 offset
            name_region = safe_slice(img, y + h + 5, 40, x - 15, w + 30)
            if name_region is None:
                print(
                    f"Skipping contour {i}: empty name region at ({x}, {y}, {w}, {h})"
                )
                continue
            name_region = cv2.resize(
                name_region, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC
            )
            # 对名字区域进行二值化处理，增强 OCR 识别效果
            name_gray = cv2.cvtColor(name_region, cv2.COLOR_BGR2GRAY)
            _, name_bin = cv2.threshold(name_gray, 200, 255, cv2.THRESH_BINARY)
            # 反色处理
            name_bin = cv2.bitwise_not(name_bin)
            # debug_show(name_bin, title=f"Name Region {i}")

            # C. 识别文字
            out = ocr.ocr_for_single_line(name_bin)
            name = out["text"].strip() if out["text"] else f"unknown_{i}"
            name = alias_fix(name)

            # 清理文件名非法字符
            name = "".join(c for c in name if c not in r'\/:*?"<>|')

            # D. 保存
            save_path = os.path.join(output_folder, f"{name}.webp")

            # 使用 imencode 将图片格式化为 webp 字节流，再写入文件
            encode_param = [int(cv2.IMWRITE_WEBP_QUALITY), 100]
            is_success, buffer = cv2.imencode(".webp", avatar, encode_param)
            if is_success:
                with open(save_path, "wb") as f:
                    f.write(buffer)
                print(f"Success: {save_path}, Score: {out['score']:.2f}")
                outputs.append(f"{filename}/{name}")
                if name in names:
                    print(f"Warning: Duplicate name detected - {name}")
                names.add(name)
            else:
                print(f"Failed to encode: {name}")
    return outputs


def debug_show(image, title="Image"):
    cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow(title, 100, 100)

    # 3. 显示图像
    cv2.imshow(title, image)
    key = cv2.waitKey(0) & 0xFF
    if key == ord("q"):
        raise KeyboardInterrupt("User requested exit.")
    cv2.destroyAllWindows()


def safe_slice(image, y, h, x, w):
    img_h, img_w = image.shape[:2]
    y1 = max(0, y)
    y2 = min(img_h, y + h)
    x1 = max(0, x)
    x2 = min(img_w, x + w)
    if y1 >= y2 or x1 >= x2:
        return None
    return image[y1:y2, x1:x2]


def update_id_json(file_path, new_outputs):
    # 1. 读取原始数据 (如果文件不存在，则初始化默认结构)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"next_id": 0, "values": []}

    # 获取已存在的名称集合，方便快速查找
    existing_names = {item["name"] for item in data["values"]}
    added_items = []

    # 2. 遍历输入的 outputs，检查是否需要新增
    for name in new_outputs:
        if name not in existing_names:
            # 根据 name 前缀（朝代/势力）自动补全 pack
            dynasty = name.split("/", 1)[0]
            pack = DYNASTY_PACK[dynasty]
            if dynasty in MULTI_PACK_DYNASTIES:
                print(
                    f"Warning: 朝代「{dynasty}」横跨多个卡包，已按主卡包填为「{pack}」，"
                    f"请人工核对 {name}"
                )
            new_entry = {"id": data["next_id"], "name": name, "pack": pack}
            data["values"].append(new_entry)
            added_items.append(new_entry)

            # 更新全局 ID 计数器
            data["next_id"] += 1

    # 3. 打印新增的内容
    if added_items:
        print("本次新增的记录如下：")
        for item in added_items:
            print(f"ID: {item['id']} -> Name: {item['name']}")

        return data, added_items
    else:
        print("所有 output 已存在，无需更新。")
        return data, []


def do_slice():
    """阶段一：OCR 切图 -> temp_output/，不触碰 assets 与 data.js。"""
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)
    os.makedirs(TEMP_FOLDER)

    outputs = []
    for filename in os.listdir(INPUT_FOLDER):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            outputs.extend(
                process_atlas(os.path.join(INPUT_FOLDER, filename), TEMP_FOLDER)
            )

    print(f"\n切图完成：{len(outputs)} 张 -> {TEMP_FOLDER}/")
    print("请核对 OCR 结果；如有误，修改 NAME_MAPPING 后重跑 slice。")
    return outputs


def collect_temp_outputs():
    outputs = []
    for folder in sorted(os.listdir(TEMP_FOLDER)):
        folder_path = os.path.join(TEMP_FOLDER, folder)
        if not os.path.isdir(folder_path):
            continue
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".webp"):
                outputs.append(f"{folder}/{os.path.splitext(filename)[0]}")
    return outputs


def do_apply():
    """阶段二：temp_output/ -> assets（只替换本次涉及的朝代）+ id.json + data.js。"""
    if not os.path.isdir(TEMP_FOLDER):
        print(f"未找到 {TEMP_FOLDER}/，请先运行 slice。")
        return

    outputs = collect_temp_outputs()
    if not outputs:
        print(f"{TEMP_FOLDER}/ 为空，请先运行 slice。")
        return

    new_data, added_items = update_id_json(ID_FILE, outputs)

    affected = sorted(
        item
        for item in os.listdir(TEMP_FOLDER)
        if os.path.isdir(os.path.join(TEMP_FOLDER, item))
    )
    print(f"\n将仅替换以下朝代目录：{', '.join(affected)}")
    confirm = (
        input(
            f"检测到 {len(added_items)} 条新记录。是否确认写入 assets 与 id.json？(y/n): "
        )
        .strip()
        .lower()
    )
    if confirm != "y":
        print("操作已取消。保持原文件不变。")
        return

    for folder in affected:
        src_path = os.path.join(TEMP_FOLDER, folder)
        dst_path = os.path.join(TARGET_FOLDER, folder)
        if os.path.exists(dst_path):
            shutil.rmtree(dst_path)
        shutil.move(src_path, dst_path)
        print(f"已更新 {dst_path}")

    with open(ID_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print(f"成功更新至 {ID_FILE}")

    write_to_target_file(new_data)


def do_data():
    """阶段三：仅由 id.json 重新生成 data.js（手动改过 id.json 后用它同步）。"""
    with open(ID_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    write_to_target_file(data)


def main():
    parser = argparse.ArgumentParser(description="mjs 头像切片工具")
    parser.add_argument(
        "action",
        choices=["slice", "apply", "data", "all"],
        help=(
            "slice=OCR切图到 temp_output；"
            "apply=写入 assets+id.json+data.js（只替换本次朝代）；"
            "data=仅由 id.json 重生成 data.js；"
            "all=slice 后立即 apply"
        ),
    )
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if args.action == "slice":
        do_slice()
    elif args.action == "apply":
        do_apply()
    elif args.action == "data":
        do_data()
    elif args.action == "all":
        do_slice()
        do_apply()


if __name__ == "__main__":
    main()
