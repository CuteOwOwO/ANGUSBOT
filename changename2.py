import os
import shutil # 用於更安全的文件操作，例如移動/重命名
import re     # 引入正則表達式模組，用於自然排序

def natural_sort_key(s):
    """
    用於實現「自然數字排序」的鍵函數。
    例如，'image10.jpg' 會排在 'image2.jpg' 之後。
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def rename_images_in_folder(folder_path, output_extension=".jpg", start_index=1):
    """
    將指定資料夾中的圖片重新命名為 i.jpg (i 為順序編號)。

    Args:
        folder_path (str): 包含圖片的資料夾路徑。
        output_extension (str): 重新命名後圖片的副檔名 (例如 ".jpg", ".png", ".webp")。
                                預設為 ".jpg"。
        start_index (int): 圖片開始編號 (i)，預設從 1 開始。
    """
    if not os.path.isdir(folder_path):
        print(f"錯誤: 資料夾 '{folder_path}' 不存在。")
        return

    print(f"正在整理資料夾: '{folder_path}' 中的圖片檔名...")

    # 支援的圖片副檔名 (可以根據需要增補)
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

    # 獲取資料夾中所有檔案的列表
    files = os.listdir(folder_path)
    
    image_files = []
    for f in files:
        if os.path.splitext(f)[1].lower() in image_extensions:
            image_files.append(f)
    
    # *** 這裡使用自然數字排序，以確保 '1', '2', '10' 的正確順序 ***
    image_files.sort(key=natural_sort_key)


    renamed_count = 0
    # 使用一個獨立的計數器來表示新的檔案編號，從 start_index 開始
    current_image_number = start_index

    for old_filename in image_files:
        # 構造舊檔案的完整路徑
        old_filepath = os.path.join(folder_path, old_filename)

        # 構造新檔案的名稱
        new_filename = f"{current_image_number}{output_extension}"
        # 構造新檔案的完整路徑
        new_filepath = os.path.join(folder_path, new_filename)

        # 如果新檔名與舊檔名相同，並且副檔名也符合，則跳過 (避免不必要的重命名)
        # 這可以處理圖片已經是 i.jpg 格式但編號不同的情況
        if old_filepath == new_filepath:
            print(f"跳過: '{old_filename}' 已經是正確的檔名。")
            current_image_number += 1 # 這種情況下也遞增編號，因為它已符合預期
            continue

        # 檢查新檔名是否已經存在，避免覆蓋
        if os.path.exists(new_filepath):
            print(f"警告: 新檔名 '{new_filename}' 已存在，跳過 '{old_filename}' 以避免覆蓋。")
            current_image_number += 1 # 這種情況下也遞增編號，因為這個新編號被佔用了
            continue

        try:
            # 執行重命名操作
            os.rename(old_filepath, new_filepath)
            print(f"成功重命名: '{old_filename}' -> '{new_filename}'")
            renamed_count += 1
            current_image_number += 1 # 成功重命名後遞增編號
        except OSError as e:
            print(f"錯誤: 無法重命名 '{old_filename}' 到 '{new_filename}': {e}")
            # 如果失敗，通常不遞增 current_image_number，以便下次可以重試或檢查
        except Exception as e:
            print(f"重命名 '{old_filename}' 時發生未知錯誤: {e}")
            # 如果失敗，通常不遞增 current_image_number

    print(f"\n整理完成。共重命名 {renamed_count} 張圖片。")
    # 注意：這裡的 len(image_files) 是指符合圖片副檔名的總數，不代表實際重命名的數量
    # renamed_count 才是真正執行了重命名的數量。
    if renamed_count < len(image_files):
        print(f"請注意: 有 {len(image_files) - renamed_count} 張圖片未被重命名 (可能因為已存在或發生錯誤)。")

# --- 執行範例 ---
if __name__ == "__main__":
    # 指定您要整理圖片的資料夾路徑
    target_folder = 'C:\\Users\\User\\Desktop\\DC\\cogs\\momomo'

    # 設定圖片開始編號的變數
    desired_start_index = 1 # 您可以將這裡改為任何您想要的起始數字，例如 100

    print(f"將把 '{target_folder}' 中的圖片重新命名為從 {desired_start_index}.jpg 開始...")
    rename_images_in_folder(target_folder, output_extension=".jpg", start_index=desired_start_index)

    # 警告：在運行此腳本之前，請務必備份您的圖片資料夾，以防萬一！