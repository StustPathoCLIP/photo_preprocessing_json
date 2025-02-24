import os
import re
import shutil

def filter_filenames(directory):
    pattern = re.compile(r"^TCGA-\w{2}-\w{4}$")  # 匹配格式 TCGA-XX-XXXX
    valid_filenames = set()
    
    for filename in os.listdir(directory):
        name, _ = os.path.splitext(filename)  # 去掉副檔名
        if pattern.fullmatch(name):
            valid_filenames.add(name)
    
    return sorted(valid_filenames)

def list_valid_folders(directory):
    pattern = re.compile(r"^(TCGA-\w{2}-\w{4})-\d$")  # 匹配格式 TCGA-XX-XXXX-X（最後為數字）
    valid_folders = set()
    
    for folder_name in os.listdir(directory):
        folder_path = os.path.join(directory, folder_name)
        match = pattern.fullmatch(folder_name)
        if os.path.isdir(folder_path) and match:
            valid_folders.add(match.group(1))  # 只保留 TCGA-XX-XXXX 部分
    
    return sorted(valid_folders)

def find_extra_folders(main_list, compare_list):
    return sorted(set(compare_list) - set(main_list))

def delete_extra_folders(extra_folders, target_directory):
    for folder in os.listdir(target_directory):
        folder_path = os.path.join(target_directory, folder)
        match = re.match(r"^(TCGA-\w{2}-\w{4})-\d$", folder)
        if match and match.group(1) in extra_folders and os.path.isdir(folder_path):
            try:
                shutil.rmtree(folder_path)
                print(f"已刪除資料夾: {folder_path}")
            except Exception as e:
                print(f"刪除失敗: {folder_path}，錯誤: {e}")
        else:
            print(f"資料夾保留: {folder_path}")

if __name__ == "__main__":
    md_directory = r"C:\\Users\\user\\Desktop\\coad\\data\\COAD\\md"
    train_directory = r"C:\\Users\\user\\Desktop\\coad\\data\\COAD\\train"
    
    # 取得符合格式的檔名與資料夾（忽略最後的 -X）
    valid_filenames = filter_filenames(md_directory)
    valid_folders = list_valid_folders(train_directory)
    
    # 找出多餘的資料夾（以 TCGA-XX-XXXX 進行比對）
    extra_folders = find_extra_folders(valid_filenames, valid_folders)
    
    # 刪除多餘的資料夾（包含所有對應的 TCGA-XX-XXXX-X）
    delete_extra_folders(extra_folders, train_directory)
