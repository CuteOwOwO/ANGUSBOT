import requests
from bs4 import BeautifulSoup
import os
import json
from PIL import Image # 引入 Pillow 函式庫

# 設定預設的下載資料夾路徑
DEFAULT_DOWNLOAD_FOLDER = "C:/Users/User/Desktop/DC/cogs/momomo2"


def download_and_convert_image(url, folder, image_index, target_extension=".jpg"):
    """
    下載圖片，並將其轉換為指定的目標格式 (例如 .jpg)，然後以 i.target_extension 格式命名。

    Args:
        url (str): 圖片的 URL。
        folder (str): 圖片儲存的資料夾路徑。
        image_index (int): 圖片的編號 (i)。
        target_extension (str): 目標副檔名 (例如 ".jpg", ".png")。
                                必須以點號開頭。
    Returns:
        str: 成功下載並轉換的檔案路徑，如果失敗則返回 None。
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 構造目標檔名 (i.target_extension)
    new_filename = f"{image_index}{target_extension}"
    filepath = os.path.join(folder, new_filename)

    # 如果目標檔案已經存在，則跳過下載和轉換
    if os.path.exists(filepath):
        print(f"目標圖片 '{new_filename}' 已存在，跳過下載和轉換。")
        return filepath

    # 臨時檔名，用於保存原始下載的圖片
    # 使用一個不容易重複的名稱，例如加上時間戳或 UUID
    temp_filename = f"temp_image_{image_index}_{os.path.basename(url).split('?')[0]}"
    temp_filepath = os.path.join(folder, temp_filename)

    try:
        # 1. 下載原始圖片到臨時檔案
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(temp_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"原始圖片下載完成: {temp_filepath}")

        # 2. 使用 Pillow 打開臨時檔案並轉換格式
        img = Image.open(temp_filepath)
        
        # 如果是動態圖片 (如動態 WebP 或 GIF)，通常只會保存第一幀
        # 對於 WebP 轉 JPG，這是正常行為。
        
        # 如果是透明背景的圖片 (例如 PNG 或某些 WebP)，轉 JPG 時需要處理透明度
        # 因為 JPG 不支援透明度。通常會將透明部分替換為白色背景。
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            print(f"檢測到透明通道，轉換為 {target_extension} 時將填充白色背景。")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else img) # 僅對 RGBA 使用透明通道
            img = background
        elif img.mode == 'P': # 對於調色板模式的圖片，轉換為 RGB
             img = img.convert('RGB')
        
        # 確保是 RGB 模式，以兼容 JPG 格式
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 3. 保存為目標格式 (例如 .jpg)
        # quality 參數用於 JPEG 壓縮質量 (0-100)，預設為 75
        img.save(filepath, quality=90) 
        print(f"成功轉換並保存: {filepath}")

        # 4. 刪除臨時檔案
        os.remove(temp_filepath)
        print(f"已刪除臨時檔案: {temp_filepath}")

        return filepath
    except requests.exceptions.RequestException as e:
        print(f"下載 {url} 時發生錯誤: {e}")
        # 如果下載失敗，確保清除可能殘留的臨時檔案
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return None
    except FileNotFoundError:
        print(f"錯誤: 找不到臨時檔案 {temp_filepath}。")
        return None
    except Exception as e:
        print(f"處理圖片 '{url}' (目標: '{new_filename}') 時發生未知錯誤: {e}")
        # 如果處理失敗，確保清除可能殘留的臨時檔案
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        return None


def parse_html_and_download_images(html_content, start_index=1, base_url="https://www.4khd.com/", output_folder=DEFAULT_DOWNLOAD_FOLDER, force_to_jpg=True):
    """
    解析 HTML 內容，尋找圖片 URL 並下載，圖片以編號命名。
    可選擇是否強制轉換為 JPG 格式。

    Args:
        html_content (str): 要解析的 HTML 內容。
        start_index (int): 圖片開始編號 (i)。
        base_url (str): 用於處理相對路徑圖片的基礎 URL。
        output_folder (str): 圖片儲存的目標資料夾。
        force_to_jpg (bool): 是否強制將圖片轉換為 JPG 格式。
    Returns:
        list: 成功下載並轉換的圖片檔案路徑列表。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    image_urls_info = [] # 儲存 (url, 原始副檔名) 元組的列表

    # 輔助函數：提取 URL 的副檔名
    def get_extension_from_url(url_str):
        return os.path.splitext(url_str.split('?')[0])[-1].lower()

    # 1. 尋找 <img> 標籤的 src 屬性
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src:
            if src.startswith('//'):
                src = "https:" + src
            elif src.startswith('/'):
                src = base_url.rstrip('/') + src
            
            original_ext = get_extension_from_url(src)
            if not original_ext: original_ext = ".jpg" # 預設副檔名
            image_urls_info.append((src, original_ext))

    # 2. 尋找 meta 標籤中的圖片 URL
    for meta_tag in soup.find_all('meta', property=lambda x: x and 'image' in x):
        content = meta_tag.get('content')
        if content and (content.startswith('http://') or content.startswith('https://')):
            original_ext = get_extension_from_url(content)
            if not original_ext: original_ext = ".jpg"
            image_urls_info.append((content, original_ext))

    # 3. 尋找 <script type="application/ld+json"> 區塊中的圖片 URL
    for script_tag in soup.find_all('script', type='application/ld+json'):
        try:
            json_data = json.loads(script_tag.string)
            # 簡化JSON處理，確保能獲取到 'url'
            if isinstance(json_data, dict):
                # 處理 '@graph' 結構
                if '@graph' in json_data and isinstance(json_data['@graph'], list):
                    for item in json_data['@graph']:
                        if isinstance(item, dict):
                            if 'url' in item: # 直接找 url
                                url = item['url']
                                original_ext = get_extension_from_url(url)
                                if not original_ext: original_ext = ".jpg"
                                image_urls_info.append((url, original_ext))
                            if 'image' in item and isinstance(item['image'], dict) and 'url' in item['image']: # 找 image.url
                                url = item['image']['url']
                                original_ext = get_extension_from_url(url)
                                if not original_ext: original_ext = ".jpg"
                                image_urls_info.append((url, original_ext))
                # 處理單個 ImageObject 或其他直接包含 image 屬性的結構
                if 'url' in json_data and json_data.get('@type') == 'ImageObject':
                    url = json_data['url']
                    original_ext = get_extension_from_url(url)
                    if not original_ext: original_ext = ".jpg"
                    image_urls_info.append((url, original_ext))
                elif 'image' in json_data and isinstance(json_data['image'], dict) and 'url' in json_data['image']:
                    url = json_data['image']['url']
                    original_ext = get_extension_from_url(url)
                    if not original_ext: original_ext = ".jpg"
                    image_urls_info.append((url, original_ext))

        except json.JSONDecodeError:
            continue

    # 去重：因為可能從多個地方找到相同的 URL。
    # 將列表轉換為集合再轉換回列表以去重，同時保持原始副檔名
    unique_image_urls_info = list(set(image_urls_info))
    print(f"找到 {len(unique_image_urls_info)} 張去重後的圖片連結。")

    downloaded_files = []
    current_index = start_index

    for img_url, original_ext in unique_image_urls_info:
        # 如果 force_to_jpg 為 True，則強制目標副檔名為 .jpg
        target_output_ext = ".jpg" if force_to_jpg else original_ext
        
        downloaded_path = download_and_convert_image(img_url, output_folder, current_index, target_output_ext)
        if downloaded_path:
            downloaded_files.append(downloaded_path)
            current_index += 1
    
    return downloaded_files


# --- 主程式流程 ---
if __name__ == "__main__":
    html_file_path = '未命名.txt' # 假設此檔案在與腳本相同的目錄
    
    if os.path.exists(html_file_path):
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"正在從檔案 '{html_file_path}' 載入 HTML 內容...")
        
        # --- 控制起始編號、下載資料夾和是否強制轉為 JPG ---
        start_image_number = 1 # 從 1 開始編號
        target_download_folder = DEFAULT_DOWNLOAD_FOLDER 
        force_convert_to_jpg = True # <--- 這裡設定為 True，表示強制轉換為 JPG
        
        # 執行圖片下載與轉換
        base_website_url = "https://www.4khd.com/"
        downloaded_images = parse_html_and_download_images(
            html_content, 
            start_index=start_image_number,
            base_url=base_website_url,
            output_folder=target_download_folder,
            force_to_jpg=force_convert_to_jpg # 將控制參數傳入
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