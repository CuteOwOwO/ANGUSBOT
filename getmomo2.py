import requests
from bs4 import BeautifulSoup
import os
import json # 雖然這次不用中文名，但載入 JSON 內容時可能遇到，所以還是保留

# 設定預設的下載資料夾路徑 (您指定的路徑)
# 請注意：在 Python 字串中，反斜線 \ 需要雙寫 \\ 或使用原始字串 r"..."
# 或者使用正斜線 /，Python 會自動轉換。這裡使用正斜線更通用。
DEFAULT_DOWNLOAD_FOLDER = "C:\\Users\\User\\Desktop\\DC\\cogs\\momomo"


def download_image_with_renaming(url, folder, image_index, original_extension=".jpg"):
    """
    下載圖片到指定資料夾，並以 i.extension 格式命名。

    Args:
        url (str): 圖片的 URL。
        folder (str): 圖片儲存的資料夾路徑。
        image_index (int): 圖片的編號 (i)。
        original_extension (str): 圖片的原始副檔名 (例如 ".jpg", ".webp")。
                                  這用於確保儲存的副檔名與原圖一致。
    Returns:
        str: 成功下載的檔案路徑，如果下載失敗則返回 None。
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 構造新的檔名 (i.副檔名)
    new_filename = f"{image_index}{original_extension}"
    filepath = os.path.join(folder, new_filename)

    # 如果檔案已經存在，則跳過下載，避免重複下載
    if os.path.exists(filepath):
        print(f"圖片 '{new_filename}' 已存在，跳過下載。")
        return filepath

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # 檢查請求是否成功

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"成功下載: {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        print(f"下載 {url} (命名為 {new_filename}) 時發生錯誤: {e}")
        return None
    except Exception as e:
        print(f"處理 {url} (命名為 {new_filename}) 時發生未知錯誤: {e}")
        return None


def parse_html_and_download_images(html_content, start_index=1, base_url="https://www.4khd.com/", output_folder=DEFAULT_DOWNLOAD_FOLDER):
    """
    解析 HTML 內容，尋找圖片 URL 並下載，圖片以編號命名。

    Args:
        html_content (str): 要解析的 HTML 內容。
        start_index (int): 圖片開始編號 (i)。
        base_url (str): 用於處理相對路徑圖片的基礎 URL。
        output_folder (str): 圖片儲存的目標資料夾。
    Returns:
        list: 成功下載的圖片檔案路徑列表。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    image_urls_info = [] # 儲存 (url, 原始副檔名) 元組的列表

    # 1. 尋找 <img> 標籤的 src 屬性
    # 針對您提供的 HTML 範例，img.4khd.com 的圖片通常是 .webp 格式
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src:
            # 處理相對路徑
            if src.startswith('//'):
                src = "https:" + src
            elif src.startswith('/'):
                src = base_url.rstrip('/') + src

            # 從 URL 中提取原始副檔名
            # 例如 "image.webp?w=1300" -> ".webp"
            original_ext = os.path.splitext(src.split('?')[0])[-1].lower()
            if not original_ext: # 如果沒有副檔名，預設為 .jpg
                original_ext = ".jpg"
            image_urls_info.append((src, original_ext))

    # 2. 尋找 meta 標籤中的圖片 URL (例如 Open Graph / Twitter Card 圖片)
    for meta_tag in soup.find_all('meta', property=lambda x: x and 'image' in x):
        content = meta_tag.get('content')
        if content and (content.startswith('http://') or content.startswith('https://')):
            original_ext = os.path.splitext(content.split('?')[0])[-1].lower()
            if not original_ext:
                original_ext = ".jpg"
            image_urls_info.append((content, original_ext))

    # 3. 尋找 <script type="application/ld+json"> 區塊中的圖片 URL
    for script_tag in soup.find_all('script', type='application/ld+json'):
        try:
            json_data = json.loads(script_tag.string)
            if isinstance(json_data, dict) and '@graph' in json_data:
                for item in json_data['@graph']:
                    if isinstance(item, dict) and item.get('@type') == 'ImageObject':
                        if 'url' in item:
                            url = item['url']
                            original_ext = os.path.splitext(url.split('?')[0])[-1].lower()
                            if not original_ext:
                                original_ext = ".jpg"
                            image_urls_info.append((url, original_ext))
                    elif isinstance(item, dict) and 'image' in item and isinstance(item['image'], dict) and 'url' in item['image']:
                        url = item['image']['url']
                        original_ext = os.path.splitext(url.split('?')[0])[-1].lower()
                        if not original_ext:
                            original_ext = ".jpg"
                        image_urls_info.append((url, original_ext))
            elif isinstance(json_data, dict) and json_data.get('@type') == 'ImageObject':
                if 'url' in json_data:
                    url = json_data['url']
                    original_ext = os.path.splitext(url.split('?')[0])[-1].lower()
                    if not original_ext:
                        original_ext = ".jpg"
                    image_urls_info.append((url, original_ext))

        except json.JSONDecodeError:
            continue

    unique_image_urls_info = list(set(image_urls_info))
    print(f"找到 {len(unique_image_urls_info)} 張去重後的圖片連結。")

    downloaded_files = []
    current_index = start_index # 從指定索引開始
    for img_url, img_ext in unique_image_urls_info:
        # 下載並直接以編號命名
        downloaded_path = download_image_with_renaming(img_url, output_folder, current_index, img_ext)
        if downloaded_path:
            downloaded_files.append(downloaded_path)
            current_index += 1 # 成功下載一張後，編號遞增
    
    # 如果您希望下載後再進行一次排序，可以使用之前提供的獨立整理檔名的函數
    # 但這裡已經在下載時直接編號，通常不需要再次整理。
    # 如果頁面圖片順序很重要，您可能需要在 unique_image_urls_info 之前對 image_urls_info 進行排序。
    return downloaded_files


# --- 主程式流程 ---
if __name__ == "__main__":
    html_file_path = '未命名.txt' # 假設此檔案在與腳本相同的目錄
    
    if os.path.exists(html_file_path):
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"正在從檔案 '{html_file_path}' 載入 HTML 內容...")
        
        # --- 控制起始編號和下載資料夾 ---
        # 設定圖片開始的編號
        start_image_number = 52 # 從 52 開始編號

        # 設定圖片下載的目標資料夾
        # 這裡直接使用 DEFAULT_DOWNLOAD_FOLDER，您也可以傳入其他路徑
        target_download_folder = DEFAULT_DOWNLOAD_FOLDER 
        
        # 執行圖片下載
        base_website_url = "https://www.4khd.com/"
        downloaded_images = parse_html_and_download_images(
            html_content, 
            start_index=start_image_number,
            base_url=base_website_url,
            output_folder=target_download_folder
        )
        
        if downloaded_images:
            print("\n所有圖片下載完成！")
            print("下載路徑:")
            for img_path in downloaded_images:
                print(f"- {img_path}")
        
        else:
            print("\n沒有圖片被下載，請檢查 HTML 內容或圖片 URL。")
            
            
    else:
        print(f"錯誤: 檔案 '{html_file_path}' 不存在。請確保檔案已上傳或路徑正確。")