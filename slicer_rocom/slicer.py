import shutil
import os
import json
import cv2
import numpy as np
import requests

TARGET_FILE = "../src_rocom/data.js"
DATA_START = "/* DATA_START */"
DATA_END = "/* DATA_END */"
DATA_TEMPLATE = "export const data = {0}"

TARGET_FOLDER = "../src_rocom/assets"
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


def update_id_json(file_path):
    # 1. 读取原始数据 (如果文件不存在，则初始化默认结构)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"next_id": 0, "values": []}

    if os.path.exists("images") == False:
        os.makedirs("images")

    # 获取已存在的名称集合，方便快速查找
    existing_names = {item["name"] for item in data["values"]}
    added_items = []

    with open("data_export.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    for entry in metadata:
        name = entry["name"]
        name = f"{entry['属性'][0]}/{name}"
        if name in existing_names:
            continue  # 已存在，无需添加
        image_url = entry.pop("img")
        # 从url中提取图片名称（不带扩展名）
        image_name = os.path.splitext(os.path.basename(image_url))[0]
        # URL编码解码
        image_name = requests.utils.unquote(image_name)
        # 检查本地images文件夹是否已经存在该图片，如果不存在则下载
        image_path = os.path.join("images", f"{image_name}.webp")
        if not os.path.exists(image_path):
            try:
                response = requests.get(image_url, stream=True)
                if response.status_code == 200:
                    with open(image_path, "wb") as img_file:
                        for chunk in response.iter_content(1024):
                            img_file.write(chunk)
                    convert_to_webp(image_path)
                    print(f"Downloaded image for {name} to {image_path}")
                else:
                    print(
                        f"Failed to download image for {name}: HTTP {response.status_code}"
                    )
            except Exception as e:
                print(f"Error downloading image for {name}: {e}")
        # 保存图片到TARGET_FOLDER
        target_image_path = os.path.join(TARGET_FOLDER, f"{name}.webp")
        os.makedirs(os.path.dirname(target_image_path), exist_ok=True)
        shutil.copy(image_path, target_image_path)

        new_entry = {"id": data["next_id"]}
        new_entry.update(entry)
        new_entry["name"] = name
        data["values"].append(new_entry)
        added_items.append(new_entry)

        # 更新全局 ID 计数器
        data["next_id"] += 1

    with open("data_export.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

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


def convert_to_webp(image_path, quality=90):
    """
    将指定路径的图片转换为 webp 格式并保存到原处
    :param image_path: 图片的完整路径
    :param quality: webp 的压缩质量 (0-100)
    """
    try:
        # 1. 使用 numpy 读取含有中文路径的图片
        # np.fromfile 可以绕过 OpenCV 对中文路径的支持限制
        img_array = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)

        if img is None:
            print(f"无法读取文件: {image_path}")
            return

        # 2. 准备输出路径（将原后缀改为 .webp）
        file_dir, file_name = os.path.split(image_path)
        name_without_ext = os.path.splitext(file_name)[0]
        output_path = os.path.join(file_dir, f"{name_without_ext}.webp")

        # 3. 使用 imencode 将图片编码为 webp 格式的字节流
        # cv2.IMWRITE_WEBP_QUALITY 用于控制质量
        success, encoded_img = cv2.imencode(
            ".webp", img, [cv2.IMWRITE_WEBP_QUALITY, quality]
        )

        if success:
            # 4. 将编码后的字节流写入文件
            encoded_img.tofile(output_path)

            # 可选：如果确信转换成功，可以删除原图
            # os.remove(image_path)
        else:
            print(f"转换失败: {image_path}")

    except Exception as e:
        print(f"处理过程中出错: {e}")


if __name__ == "__main__":
    # 获取当前脚本的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 切换当前工作目录
    os.chdir(script_dir)

    init_output_folder(TARGET_FOLDER, TARGET_FOLDER_WHITELIST)
    data = update_id_json("id.json")
    write_to_target_file(data)
