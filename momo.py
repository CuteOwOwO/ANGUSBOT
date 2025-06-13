import requests
from bs4 import BeautifulSoup
import os
import json # 雖然這次不用中文名，但載入 JSON 內容時可能遇到，所以還是保留


def download_image(url, folder="C:\\Users\\User\\Desktop\\DC\\momomo"):
    """下載圖片到指定資料夾"""
    if not os.path.exists(folder):
        os.makedirs(folder)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # 檢查請求是否成功

        # 從 URL 中提取檔名，如果 URL 太複雜，可能需要更複雜的邏輯
        filename = os.path.join(folder, url.split('/')[-1].split('?')[0])

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"成功下載: {filename}")
        return filename
    except requests.exceptions.RequestException as e:
        print(f"下載 {url} 時發生錯誤: {e}")
        return None
    except Exception as e:
        print(f"處理 {url} 時發生未知錯誤: {e}")
        return None

def parse_html_and_download_images(html_content, base_url="https://www.4khd.com/"):
    """
    解析 HTML 內容，尋找圖片 URL 並下載。
    base_url 用於處理相對路徑的圖片。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    image_urls = set() # 使用集合避免重複下載

    # 1. 尋找 <img> 標籤的 src 屬性
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if src:
            # 處理相對路徑
            if src.startswith('//'): # 例如 //img.example.com/image.jpg
                src = "https:" + src
            elif src.startswith('/'): # 例如 /images/image.jpg
                src = base_url.rstrip('/') + src # 確保 base_url 末尾沒有斜線
            image_urls.add(src)

    # 2. 尋找 meta 標籤中的圖片 URL (例如 Open Graph / Twitter Card 圖片)
    for meta_tag in soup.find_all('meta', property=lambda x: x and 'image' in x):
        content = meta_tag.get('content')
        if content and (content.startswith('http://') or content.startswith('https://')):
            image_urls.add(content)

    # 3. 尋找 <script type="application/ld+json"> 區塊中的圖片 URL
    for script_tag in soup.find_all('script', type='application/ld+json'):
        try:
            json_data = json.loads(script_tag.string)
            # 檢查是否為 ImageObject 或包含圖片的結構
            if isinstance(json_data, dict) and '@graph' in json_data:
                for item in json_data['@graph']:
                    if isinstance(item, dict) and item.get('@type') == 'ImageObject':
                        if 'url' in item:
                            image_urls.add(item['url'])
                    elif isinstance(item, dict) and 'image' in item and isinstance(item['image'], dict) and 'url' in item['image']:
                        image_urls.add(item['image']['url'])
            elif isinstance(json_data, dict) and json_data.get('@type') == 'ImageObject':
                if 'url' in json_data:
                    image_urls.add(json_data['url'])

        except json.JSONDecodeError:
            continue # 如果不是有效的 JSON，則跳過

    print(f"找到 {len(image_urls)} 張圖片連結。")

    downloaded_files = []
    for img_url in image_urls:
        downloaded_path = download_image(img_url)
        if downloaded_path:
            downloaded_files.append(downloaded_path)
    return downloaded_files


# --- 主程式流程 ---
if __name__ == "__main__":
    # 這裡將使用您提供的 '未命名.txt' 內容
    # 在實際應用中，您可以從網路請求獲取 HTML
    html_file_path = '未命名.txt' # 假設此檔案在與腳本相同的目錄
    
    if os.path.exists(html_file_path):
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"正在從檔案 '{html_file_path}' 載入 HTML 內容...")
        
        # 執行圖片下載
        # 這裡設定一個基礎 URL，用於解析相對路徑。
        # 您提供的 HTML 內容中，原始網站是 "https://www.4khd.com"
        base_website_url = "https://www.4khd.com/"
        downloaded_images = parse_html_and_download_images(html_content, base_url=base_website_url)
        
        if downloaded_images:
            print("\n所有圖片下載完成！")
            print("下載路徑:")
            for img_path in downloaded_images:
                print(f"- {img_path}")
        else:
            print("\n沒有圖片被下載，請檢查 HTML 內容或圖片 URL。")
            
    else:
        print(f"錯誤: 檔案 '{html_file_path}' 不存在。請確保檔案已上傳或路徑正確。")