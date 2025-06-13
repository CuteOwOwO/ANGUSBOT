import requests
from bs4 import BeautifulSoup
import os
import re
import json # 引入 json 模組，用於保存字典

def download_ourocg_card_images_numbered(search_term, output_folder="C:\\Users\\User\\Desktop\\DC\\cogs\\cards"):
    """
    從 ourocg.cn 搜尋卡牌並下載其圖片，以 cardN.jpg 命名，
    並將圖片編號與中文名稱記錄在字典中。

    Args:
        search_term (str): 要搜尋的卡牌名稱 (例如: "閃刀姬")。
        output_folder (str): 儲存圖片和 JSON 檔案的資料夾名稱。
    """
    encoded_search_term = requests.utils.quote(search_term)
    url = f"https://ygocdb.com/?search={encoded_search_term}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"正在訪問: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"訪問網站時發生錯誤: {e}")
        return

    ##把抓到的HTML字串原始碼用成soup(物件名稱)
    soup = BeautifulSoup(response.text, "html.parser")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"已創建資料夾: {output_folder}")
    else:
        print(f"資料夾 '{output_folder}' 已存在。")

    card_results = soup.find_all("div", class_="row card result")

    if not card_results:
        print(f"在 {url} 中找不到卡牌結果。請檢查網站結構或搜尋詞是否正確。")
        return

    print(f"找到 {len(card_results)} 張卡牌資訊，開始下載圖片並記錄名稱...")

    # 初始化一個字典來記錄卡牌名稱
    # 鍵(key)是圖片的檔名 (例如: 'card1.jpg')，值(value)是中文卡牌名稱
    card_names_map = {}
    
    # 初始化圖片編號
    card_counter = 1

    for card_div in card_results:
        # 定位圖片 URL
        img_tag = card_div.find("img", loading="lazy", src=lambda src: src and "cdn.233.momobako.com/ygopro/pics/" in src)
        if not img_tag:
            continue

        img_url = img_tag.get("src")
        if not img_url:
            continue

        # 定位卡牌中文名稱
        name_tag = card_div.find("h2").find("span", lang="zh-Hans")
        card_chinese_name = ""
        if name_tag:
            card_chinese_name = name_tag.get_text(strip=True)

        # 如果沒有找到中文名稱，可以跳過或給一個預設值，這裡我們給一個「未知卡牌」的標記
        if not card_chinese_name:
            print(f"警告: 未找到圖片 '{img_url}' 的中文名稱。將使用 '未知卡牌' 佔位。")
            card_chinese_name = "未知卡牌"
        
        # 構建新的檔名 (cardN.jpg)
        new_file_name = f"card{card_counter}.jpg"
        file_path = os.path.join(output_folder, new_file_name)

        try:
            # 檢查圖片是否已經存在，避免重複下載
            if os.path.exists(file_path):
                print(f"圖片 '{new_file_name}' 已存在，跳過下載。")
            else:
                img_data = requests.get(img_url, headers=headers, stream=True)
                img_data.raise_for_status()

                with open(file_path, "wb") as f:
                    for chunk in img_data.iter_content(1024):
                        f.write(chunk)
                print(f"成功下載: {new_file_name}")
            
            # 將編號和中文名稱加入字典
            card_names_map[new_file_name] = card_chinese_name
            # 圖片下載成功或已存在後，計數器加一
            card_counter += 1

        except requests.exceptions.RequestException as e:
            print(f"下載圖片 '{img_url}' (命名為 '{new_file_name}') 時發生錯誤: {e}")
        except Exception as e:
            print(f"處理圖片 '{img_url}' (命名為 '{new_file_name}') 時發生未知錯誤: {e}")

    # 下載完成後，將卡牌名稱字典保存為 JSON 文件
    json_file_path = os.path.join(output_folder, f"{search_term}_card_names.json")
    try:
        # ensure_ascii=False 讓中文字符能正確地被寫入 JSON 文件，而不是轉為 Unicode 編碼。
        # indent=4 讓 JSON 文件格式化，方便閱讀。
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(card_names_map, f, ensure_ascii=False, indent=4)
        print(f"卡牌名稱對應字典已保存至: {json_file_path}")
    except Exception as e:
        print(f"保存卡牌名稱字典時發生錯誤: {e}")

# 執行範例
if __name__ == "__main__":
    download_ourocg_card_images_numbered("閃刀姬")
    # 你可以嘗試搜尋其他卡牌，例如：
    # download_ourocg_card_images_numbered("青眼白龍")