import os
import shutil # 用於更安全的文件操作，例如移動/重命名

def rename_images_in_folder(folder_path, output_extension=".jpg"):
    """
    將指定資料夾中的圖片重新命名為 i.jpg (i 為順序編號)。

    Args:
        folder_path (str): 包含圖片的資料夾路徑。
        output_extension (str): 重新命名後圖片的副檔名 (例如 ".jpg", ".png", ".webp")。
                                預設為 ".jpg"。
    """
    if not os.path.isdir(folder_path):
        print(f"錯誤: 資料夾 '{folder_path}' 不存在。")
        return

    print(f"正在整理資料夾: '{folder_path}' 中的圖片檔名...")

    # 支援的圖片副檔名 (可以根據需要增補)
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

    # 獲取資料夾中所有檔案的列表
    files = os.listdir(folder_path)

    # 過濾出圖片檔案，並對其進行排序 (可選，但有助於保持一致的順序)
    # 這裡可以根據檔名、修改時間等進行排序。
    # 如果希望圖片的順序是依賴於原始檔名，可以先對 files 進行排序
    # files.sort()
    
    image_files = []
    for f in files:
        # os.path.splitext() 會將檔名和副檔名分開，例如 "image.jpg" -> ("image", ".jpg")
        # 然後將副檔名轉為小寫以便於比較
        if os.path.splitext(f)[1].lower() in image_extensions:
            image_files.append(f)
    
    # 根據檔名排序，確保重新命名時的順序是可預期的
    # 如果原始檔名是 "card1.jpg", "card10.jpg", "card2.jpg"
    # 直接排序會變成 "card1.jpg", "card10.jpg", "card2.jpg"
    # 這裡使用自然的數字排序 (natural sort) 可以使其變成 "card1.jpg", "card2.jpg", "card10.jpg"
    # 但為了簡潔，我們假設檔名已經是簡單的數字序，或者您不介意簡單的字母序。
    # 這裡我們使用簡單的字母排序，這對於 "card1", "card2", "card10" 會有點問題，
    # 但對於完全隨機的檔名，或者從 "card001", "card002" 這樣格式的，則有效。
    # 如果需要嚴格的數字排序，需要額外引入庫或編寫自然排序函數。
    image_files.sort()


    renamed_count = 0
    for i, old_filename in enumerate(image_files):
        # 構造舊檔案的完整路徑
        old_filepath = os.path.join(folder_path, old_filename)

        # 構造新檔案的名稱 (從 1 開始編號)
        new_filename = f"{i + 1}{output_extension}"
        # 構造新檔案的完整路徑
        new_filepath = os.path.join(folder_path, new_filename)

        # 如果新檔名與舊檔名相同，則跳過 (避免不必要的重命名)
        if old_filepath == new_filepath:
            print(f"跳過: '{old_filename}' 已經是正確的檔名。")
            continue

        # 檢查新檔名是否已經存在，避免覆蓋
        if os.path.exists(new_filepath):
            print(f"警告: 新檔名 '{new_filename}' 已存在，跳過 '{old_filename}' 以避免覆蓋。")
            continue

        try:
            # 執行重命名操作
            os.rename(old_filepath, new_filepath)
            print(f"成功重命名: '{old_filename}' -> '{new_filename}'")
            renamed_count += 1
        except OSError as e:
            print(f"錯誤: 無法重命名 '{old_filename}' 到 '{new_filename}': {e}")
        except Exception as e:
            print(f"重命名 '{old_filename}' 時發生未知錯誤: {e}")

    print(f"\n整理完成。共重命名 {renamed_count} 張圖片。")
    if renamed_count < len(image_files):
        print(f"請注意: 有 {len(image_files) - renamed_count} 張圖片未被重命名 (可能因為已存在或發生錯誤)。")

# --- 執行範例 ---
if __name__ == "__main__":
    # 指定您要整理圖片的資料夾路徑
    # 請將 'your_image_folder' 替換為您的實際資料夾名稱
    # 例如: 'downloaded_images' 或 'ourocg_cards_numbered'
    
    # 假設您的圖片在當前腳本所在的目錄下的 'downloaded_images' 資料夾
    target_folder = 'C:\\Users\\User\\Desktop\\DC\\momomo'

    # 或者您可以指定一個絕對路徑，例如：
    # target_folder = 'C:/Users/YourUser/Pictures/MyDownloadImages'
    # target_folder = '/home/user/images/my_downloads'

    rename_images_in_folder(target_folder, output_extension=".jpg")
    # 如果您的圖片主要是 .webp 格式，可以這樣指定：
    # rename_images_in_folder(target_folder, output_extension=".webp")

    # 警告：在運行此腳本之前，請務必備份您的圖片資料夾，以防萬一！