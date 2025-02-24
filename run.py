import os
import re
import json
import shutil
import cv2
import numpy as np
import concurrent.futures
import random
from collections import defaultdict

# 設定影像資料夾與 caption 檔案路徑
train_root = r"C:\Users\user\Desktop\coad\data\COAD\train"
md_root = r"C:\Users\user\Desktop\coad\data\COAD\md"
output_json = r"C:\Users\user\Desktop\coad\data\COAD\annotations\train_caption_tcgaCOAD.json"

# ===============================
# Step 1: 重新命名影像資料夾 (image_folder_name.py)
# ===============================

folders = sorted(os.listdir(train_root))
folder_count = {}

for folder in folders:
    folder_path = os.path.join(train_root, folder)
    if not os.path.isdir(folder_path):
        continue

    match = re.match(r"^(TCGA-\w\w-\w{4})", folder)
    if not match:
        print(f"⚠️ 無法解析資料夾名稱: {folder}")
        continue

    base_name = match.group(1)
    folder_count.setdefault(base_name, 0)
    folder_count[base_name] += 1

    new_folder_name = f"{base_name}-{folder_count[base_name]}"
    new_folder_path = os.path.join(train_root, new_folder_name)

    try:
        os.rename(folder_path, new_folder_path)
        print(f"✅ {folder} → {new_folder_name}")
    except Exception as e:
        print(f"❌ 無法重新命名 {folder}: {e}")

print("\n🎉 資料夾名稱修改完成！")

# ===============================
# Step 2: 重新命名影像檔案 (image_file_name.py)
# ===============================

base_folders = defaultdict(list)

for folder in os.listdir(train_root):
    folder_path = os.path.join(train_root, folder)
    if not os.path.isdir(folder_path):
        continue
    base_id = "-".join(folder.split("-")[:3])
    base_folders[base_id].append(folder_path)

for base_id, folder_list in sorted(base_folders.items()):
    global_index = 0
    print(f"\n🔄 開始處理: {base_id}")
    
    for folder_path in sorted(folder_list):
        images = sorted(os.listdir(folder_path))
        
        for image in images:
            image_path = os.path.join(folder_path, image)
            if not image.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            global_index += 1
            new_image_name = f"{base_id}-{global_index}.jpg"
            new_image_path = os.path.join(folder_path, new_image_name)

            try:
                os.rename(image_path, new_image_path)
                print(f"✅ {image} → {new_image_name}")
            except Exception as e:
                print(f"❌ 無法重新命名 {image}: {e}")

print("\n🎉 圖片檔名修改完成！")

# ===============================
# Step 3: 刪除不完整的資料 (delete_all.py)
# ===============================
# 這部分原本是第三步，現在提前執行

exec(open("delete_all.py", encoding="utf-8").read())

# ===============================
# Step 4: 篩選圖片並重新命名 (fire_image.py)
# ===============================
# 這部分是新增的第四步

exec(open("fire_image.py", encoding="utf-8").read())

# ===============================
# Step 5: 生成 JSON (make_json.py)
# ===============================
# 原本的第三步，現在移到第五步

HEADERS = [
    "Histologic type：",
    "Histologic grade：",
    "Primary tumor (pT)：",
    "FINAL DIAGNOSIS："
]

def clean_caption(text):
    """
    1. 標題不變
    2. 每段結束時加上「.」
    3. 如果標題內有多行，合併成一行
    4. `FINAL DIAGNOSIS：` 多行內容之間用 `, ` 連接
    """
    lines = text.strip().split("\n")
    formatted_caption = []
    current_section = ""
    is_final_diagnosis = False
    final_diagnosis_content = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if any(line.startswith(header) for header in HEADERS):
            if current_section and not is_final_diagnosis:
                formatted_caption.append(current_section.rstrip(",") + ".")

            current_section = line
            is_final_diagnosis = line.startswith("FINAL DIAGNOSIS：")
            final_diagnosis_content = []
        else:
            line = line.lstrip("-").strip()
            if is_final_diagnosis:
                final_diagnosis_content.append(line)
            else:
                current_section += " " + line if current_section else line

    if is_final_diagnosis and final_diagnosis_content:
        final_diagnosis_text = "FINAL DIAGNOSIS： " + ", ".join(final_diagnosis_content) + "."
        formatted_caption.append(final_diagnosis_text)
    elif current_section:
        formatted_caption.append(current_section.rstrip(",") + ".")

    return " ".join(formatted_caption)

captions = {}
for md_file in os.listdir(md_root):
    if md_file.endswith(".md"):
        base_name = os.path.splitext(md_file)[0]
        if base_name.endswith(("a", "b")):
            print(f"🚫 跳過 Caption: {md_file}")
            continue
        md_path = os.path.join(md_root, md_file)

        with open(md_path, "r", encoding="utf-8") as f:
            captions[base_name] = clean_caption(f.read())

print(f"✅ 讀取 {len(captions)} 份有效 caption")

annotations = []
annotation_id = 1
image_folder_count = defaultdict(int)
image_counter = defaultdict(int)

for folder in sorted(os.listdir(train_root)):
    folder_path = os.path.join(train_root, folder)
    if not os.path.isdir(folder_path):
        continue

    parts = folder.split("-")
    if len(parts) < 3:
        continue
    base_image_id = "-".join(parts[:3])

    if base_image_id not in captions:
        print(f"⚠️ 找不到對應的 caption: {base_image_id}，跳過")
        continue

    if folder.endswith(("a", "b")):
        print(f"🚫 跳過含有 a/b 的影像資料夾: {folder}")
        continue

    for image_file in sorted(os.listdir(folder_path)):
        if image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_counter[base_image_id] += 1
            new_image_id = f"{base_image_id}-{image_counter[base_image_id]}"

            annotation = {
                "image_id": new_image_id,
                "id": annotation_id,
                "caption": captions[base_image_id]
            }
            annotations.append(annotation)
            annotation_id += 1

with open(output_json, "w", encoding="utf-8") as f:
    json.dump(annotations, f, indent=4, ensure_ascii=False)

print(f"✅ JSON 已儲存：{output_json}，共 {len(annotations)} 筆資料")
