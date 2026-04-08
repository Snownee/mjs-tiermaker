import cv2
from cnocr import CnOcr
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
    "珂莱塔": ["珂菜塔"],
    "坎特蕾拉": ["坎特营拉"],
    "千咲": ["千联"],
    "漂泊者-女-湮灭": ["漂泊者-女-潭灭"],
    "漂泊者-男-湮灭": ["漂泊者-男-潭灭"],
    "吟霖": ["呤霖"],
    "今汐": ["令汐"],
    "莫特斐": ["莫特悲"],
    "炽霞": ["炽蛋"],
    "白芷": ["白在"],
    "釉瑚": ["种瑚"],
    "秧秧": ["积积"],
    "卜灵": ["上员"],
    # 在这里继续添加你遇到的生僻字或错误识别对
}

TARGET_FILE = "../src_ww/data.js"
DATA_START = "/* DATA_START */"
DATA_END = "/* DATA_END */"
DATA_TEMPLATE = "export const data = {0}"

TARGET_FOLDER = "../src_ww/assets"
TARGET_FOLDER_WHITELIST = []


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

    if raw_name.startswith("漂泊者"):
        raw_name = raw_name.replace("·", "-")

    # 1. 直接检查映射表
    for correct_name, aliases in NAME_MAPPING.items():
        if raw_name == correct_name or raw_name in aliases:
            return correct_name

    # 2. 模糊匹配：计算识别结果与所有正确名字的相似度
    # 如果相似度高于 0.6，则认为是该角色
    all_correct_names = list(NAME_MAPPING.keys())
    matches = difflib.get_close_matches(raw_name, all_correct_names, n=1, cutoff=0.6)

    if matches:
        return matches[0]

    return raw_name


def init_output_folder(folder="output", whitelist=[]):
    if os.path.exists(folder) == False:
        os.makedirs(folder)
    for item in os.listdir(folder):
        item_path = os.path.join(folder, item)
        if item in whitelist:
            print(f"Skipping {item_path} (whitelisted)")
            continue
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"Deleted folder: {item_path}")


def process_atlas(image_path, output_folder="output"):
    print(f"Processing: {image_path}")
    outputs = []

    # 获取路径中不含扩展名的文件名
    filename = os.path.splitext(os.path.basename(image_path))[0]
    # 删除filename中的数字
    filename = "".join(c for c in filename if not c.isdigit())
    output_folder = os.path.join(output_folder, filename)
    os.makedirs(output_folder, exist_ok=True)

    # 1. 读取并转换
    img_array = np.fromfile(image_path, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # 转换为 HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 2. 定义绿色的 HSV 范围 (需要根据实际图片微调)
    # 这个范围通常比较宽，以适应不同的绿色
    lower_green = np.array([35, 43, 46])  # H(色调), S(饱和度), V(亮度)
    upper_green = np.array([77, 255, 255])

    # 3. 创建掩膜 (只有绿色区域是白色)
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # 4. 反转掩膜 (使头像和名字栏区域变为白色)
    mask_inv = cv2.bitwise_not(mask)

    # (可选) 形态学操作：去除小噪点，填充微小空隙
    kernel = np.ones((3, 3), np.uint8)
    mask_inv = cv2.morphologyEx(mask_inv, cv2.MORPH_OPEN, kernel)  # 开运算去噪
    mask_inv = cv2.morphologyEx(mask_inv, cv2.MORPH_CLOSE, kernel)  # 闭运算填充

    # 5. 寻找轮廓
    contours, _ = cv2.findContours(mask_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    names = set()

    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)

        # 过滤掉非头像的小区域 (根据实际头像像素大小调整)
        if w > 100 and h > 100:
            # A. 裁剪头像本体
            avatar = img[y : y + h, x : x + w]
            # debug_show(avatar)

            # B. 裁剪名字区域 (假设名字在头像下方 5-35 像素位置)
            # 你可以根据实际图片的行间距微调这个 offset
            name_region = safe_slice(img, y + h + 5, 40, x - 15, w + 30)
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
            encode_param = [int(cv2.IMWRITE_WEBP_QUALITY), 90]
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
            new_entry = {"id": data["next_id"], "name": name}
            data["values"].append(new_entry)
            added_items.append(new_entry)

            # 更新全局 ID 计数器
            data["next_id"] += 1

    with open("data_export.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)["cards"]
    for value in data["values"]:
        raw_name = value["name"]
        name = raw_name[raw_name.find("/") + 1 :]
        value.update(metadata[name])
        value["name"] = raw_name
        value.pop("稀有度")

    # 3. 打印新增的内容
    if added_items:
        print("本次新增的记录如下：")
        for item in added_items:
            print(f"ID: {item['id']} -> Name: {item['name']}")

        # 4. 保存回原文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n成功更新至 {file_path}")
        return data
    else:
        print("所有 output 已存在，无需更新。")
        return data


if __name__ == "__main__":
    # 获取当前脚本的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 切换当前工作目录
    os.chdir(script_dir)

    outputs = []
    init_output_folder(TARGET_FOLDER, TARGET_FOLDER_WHITELIST)
    # 处理input文件夹中的所有图片
    for filename in os.listdir("input"):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            outputs.extend(
                process_atlas(os.path.join("input", filename), TARGET_FOLDER)
            )
    if len(outputs) > 0:
        data = update_id_json("id.json", outputs)
        if data:
            write_to_target_file(data)
