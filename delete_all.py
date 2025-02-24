import os
import shutil

# 設定路徑（最終檔案位置在 train 資料夾）
train_root = r"C:\Users\ZIA\Desktop\coad\data\COAD\train"
output_missing_captions = r"C:\Users\ZIA\Desktop\coad\missing_captions.txt"
output_missing_images = r"C:\Users\ZIA\Desktop\coad\missing_images.txt"
output_filtered = r"C:\Users\ZIA\Desktop\coad\filtered_missing_captions.txt"

# 由 train 資料夾中所有資料夾（格式：TCGA-XX-XXXX-X）取得影像 base id
captions = set()
for folder in os.listdir(train_root):
    # 確認是資料夾
    folder_path = os.path.join(train_root, folder)
    if not os.path.isdir(folder_path):
        continue
    # 從資料夾名稱取得 base id (TCGA-XX-XXXX)
    parts = folder.split("-")
    if len(parts) < 4:
        continue  # 格式不符的跳過
    base_id = "-".join(parts[:3])
    captions.add(base_id)

print(f"✅ 從資料夾讀取到 {len(captions)} 個 base id")

# 讀取所有影像檔案的完整 id（每個影像檔案名稱格式：TCGA-XX-XXXX-X）
image_ids = set()
for folder in os.listdir(train_root):
    folder_path = os.path.join(train_root, folder)
    if not os.path.isdir(folder_path):
        continue  # 跳過非資料夾
    
    for image_file in os.listdir(folder_path):
        if image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_id = os.path.splitext(image_file)[0]  # 去掉副檔名
            image_ids.add(image_id)

print(f"✅ 讀取到 {len(image_ids)} 份影像資料")

# 根據 image_ids 取得所有 base id（從影像檔案名稱中取得 TCGA-XX-XXXX）
image_base_ids = set()
for image_id in image_ids:
    parts = image_id.split("-")
    if len(parts) < 4:
        continue
    base_id = "-".join(parts[:3])
    image_base_ids.add(base_id)

# 找出缺少的部分
# 缺少 caption 的：有圖片但對應的 base id 不在 captions 裡
missing_captions = sorted(image_base_ids - captions)
# 缺少圖片的：有 caption 的 base id，但資料夾中卻沒有對應 base id（依照 image_ids 的 base id）
missing_images = sorted(captions - image_base_ids)

# 輸出到 missing_captions.txt
with open(output_missing_captions, "w", encoding="utf-8") as f:
    f.write("\n".join(missing_captions))

# 輸出到 missing_images.txt
with open(output_missing_images, "w", encoding="utf-8") as f:
    f.write("\n".join(missing_images))

print(f"📂 檢查完成！")
print(f"✅ 缺少 caption 的 base id 已儲存至：{output_missing_captions}，共 {len(missing_captions)} 筆")
print(f"✅ 缺少影像的 caption base id 已儲存至：{output_missing_images}，共 {len(missing_images)} 筆")

# 過濾 missing_captions.txt （其內容已經是 base id）
# 直接讀取並排序後儲存
with open(output_missing_captions, "r", encoding="utf-8") as f:
    unique_ids = sorted(set(line.strip() for line in f if line.strip()))

with open(output_filtered, "w", encoding="utf-8") as f:
    f.write("\n".join(unique_ids))

print(f"✅ 過濾後的缺少 caption 清單已儲存至：{output_filtered}，共 {len(unique_ids)} 筆資料")

# 根據 filtered_missing_captions.txt 刪除資料夾
with open(output_filtered, "r", encoding="utf-8") as f:
    missing_ids = set(line.strip() for line in f if line.strip())

print(f"✅ 讀取 {len(missing_ids)} 筆需要刪除的資料夾 base id")

# 統計刪除狀態
deleted_folders = []
not_found = []

for folder in os.listdir(train_root):
    folder_path = os.path.join(train_root, folder)
    if not os.path.isdir(folder_path):
        continue  # 跳過非資料夾
    
    # 取得該資料夾的 base id
    parts = folder.split("-")
    if len(parts) < 4:
        continue
    base_id = "-".join(parts[:3])
    
    if base_id in missing_ids:
        try:
            shutil.rmtree(folder_path)  # 刪除整個資料夾
            deleted_folders.append(folder)
            print(f"🗑️ 已刪除: {folder}")
        except Exception as e:
            print(f"❌ 刪除失敗: {folder} - {e}")
    else:
        not_found.append(folder)

print("\n🎉 資料夾刪除完成！")
print(f"✅ 成功刪除: {len(deleted_folders)} 個資料夾")
print(f"❌ 未匹配的資料夾: {len(not_found)} 個")
