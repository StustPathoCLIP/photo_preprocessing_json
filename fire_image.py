import os
import re
import shutil
import cv2
import numpy as np
import concurrent.futures
import random

# === 設定參數 ===
TARGET_DIR = r"C:\Users\ZIA\Desktop\coad\data\COAD\train"  # 來源資料夾（要篩選的資料夾）
TARGET_IMAGE_COUNT = 200  # 每組 TCGA-XX-XXXX 保留 200 張圖片
DELETE_EMPTY_FOLDERS = True  # 是否刪除空資料夾
REMOVE_FULL_WHITE = True  # 是否強制刪除 99% 以上全白的圖片
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif']  # 支援的圖片格式
NUM_THREADS = min(8, os.cpu_count() or 4)  # 最大執行緒數量（最多 8 或 CPU 核心數）

def get_tcga_groups(root_dir):
    """
    掃描符合 TCGA-XX-XXXX-X 命名規則的資料夾，並分組
    """
    pattern = re.compile(r"(TCGA-\w{2}-\w{4})-(\d+)")
    tcga_groups = {}

    for folder in sorted(os.listdir(root_dir)):
        match = pattern.match(folder)
        if match:
            base_id, folder_number = match.groups()
            folder_path = os.path.join(root_dir, folder)

            if os.path.isdir(folder_path):
                if base_id not in tcga_groups:
                    tcga_groups[base_id] = []
                tcga_groups[base_id].append((folder, int(folder_number), folder_path))

    for key in tcga_groups:
        tcga_groups[key] = sorted(tcga_groups[key], key=lambda x: x[1])

    return tcga_groups

def calculate_white_ratio(image_path):
    """
    計算圖片的白色區域比例
    """
    image = cv2.imread(image_path)  # 讀取原始圖片（RGB）
    if image is None:
        return 100  # 若圖片讀取失敗，視為 100% 空白

    # 轉換為灰階
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 自適應閥值
    thresholded = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)

    # 計算白色區域比例
    white_pixels = np.sum(thresholded == 255)
    total_pixels = gray.shape[0] * gray.shape[1]

    white_ratio = (white_pixels / total_pixels) * 100
    return white_ratio

def delete_empty_images(root_dir):
    """
    刪除全白圖片（白色比例 >= 99%）
    """
    print("🔍 正在刪除全白圖片...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        for folder, _, files in os.walk(root_dir):
            for file in files:
                if os.path.splitext(file)[1].lower() in IMAGE_EXTENSIONS:
                    img_path = os.path.join(folder, file)
                    executor.submit(check_and_delete_image, img_path)

def check_and_delete_image(img_path):
    """
    若圖片為全白，則刪除
    """
    white_ratio = calculate_white_ratio(img_path)
    if REMOVE_FULL_WHITE and white_ratio >= 99:
        print(f"❌ 刪除全白圖片: {img_path}（白色比例 {white_ratio:.2f}%）")
        os.remove(img_path)

def copy_image(old_path, new_path):
    """
    多執行緒處理圖片搬移
    """
    shutil.copy(old_path, new_path)
    print(f"✔ Copied: {old_path} → {new_path}")

def filter_and_rename_images(root_dir):
    """
    依據篩選條件隨機選取圖片，並重新命名
    """
    tcga_groups = get_tcga_groups(root_dir)

    for base_id, folders in tcga_groups.items():
        all_images = []

        # 收集所有圖片
        for folder_name, folder_number, folder_path in folders:
            images = sorted([img for img in os.listdir(folder_path) 
                             if os.path.splitext(img)[1].lower() in IMAGE_EXTENSIONS])
            for img in images:
                img_path = os.path.join(folder_path, img)
                all_images.append((folder_path, img))

        # 隨機選擇 200 張圖片
        random.shuffle(all_images)
        selected_images = all_images[:TARGET_IMAGE_COUNT]

        if len(selected_images) < TARGET_IMAGE_COUNT:
            print(f"⚠️ {base_id} 內符合條件的圖片數量不足 {TARGET_IMAGE_COUNT} 張，僅找到 {len(selected_images)} 張")

        # 創建對應的 TCGA-XX-XXXX 資料夾
        output_tcga_folder = os.path.join(root_dir, base_id)
        os.makedirs(output_tcga_folder, exist_ok=True)

        # 重新命名並存放（多執行緒搬移）
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
            futures = []
            for idx, (folder_path, img) in enumerate(selected_images, start=1):
                img_ext = os.path.splitext(img)[1].lower()
                new_filename = f"{base_id}-{idx}{img_ext}"
                new_path = os.path.join(output_tcga_folder, new_filename)
                old_path = os.path.join(folder_path, img)

                futures.append(executor.submit(copy_image, old_path, new_path))

            concurrent.futures.wait(futures)  # 等待所有複製作業完成

def delete_old_folders(root_dir):
    """
    刪除所有 `TCGA-XX-XXXX-1`, `TCGA-XX-XXXX-2` 等舊資料夾
    只保留 `TCGA-XX-XXXX`
    """
    pattern = re.compile(r"(TCGA-\w{2}-\w{4})-(\d+)")
    
    for folder in os.listdir(root_dir):
        folder_path = os.path.join(root_dir, folder)
        if os.path.isdir(folder_path):
            match = pattern.match(folder)
            if match:
                print(f"🗑 刪除舊資料夾: {folder_path}")
                shutil.rmtree(folder_path, ignore_errors=True)

if __name__ == "__main__":
    delete_empty_images(TARGET_DIR)  # 先刪除全白圖片
    filter_and_rename_images(TARGET_DIR)  # 然後篩選並重新命名
    delete_old_folders(TARGET_DIR)  # 刪除舊的 `TCGA-XX-XXXX-X` 資料夾
    print("✅ 圖片篩選與重新編號完成！（最終版本 🚀）")
