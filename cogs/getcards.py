import discord
from discord.ext import commands
import os # 導入 os 模組，用於處理檔案路徑
import random
# from random import sample # 這個沒有用到，可以移除以保持程式碼整潔
import json

# --- 1. 定義載入 JSON 的函數 ---
def load_card_names_map(json_file_path):
    """
    載入包含卡牌檔名和中文名稱對應關係的 JSON 檔案，並返回字典。
    """
    if not os.path.exists(json_file_path):
        print(f"錯誤: JSON 檔案 '{json_file_path}' 不存在。")
        return {} # 返回空字典表示載入失敗

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            card_names_data = json.load(f)
        print(f"成功載入卡牌名稱數據: {json_file_path}")
        return card_names_data
    except json.JSONDecodeError as e:
        print(f"錯誤: 無法解析 JSON 檔案 '{json_file_path}': {e}")
        return {}
    except Exception as e:
        print(f"載入檔案 '{json_file_path}' 時發生未知錯誤: {e}")
        return {}

# --- 2. 在程式一開始載入卡牌名稱字典 ---
# 注意：這個 JSON 載入是在 Cog 類別定義之外執行的。
# 如果這個 Cog 是由 main.py 載入的，那麼這裡的 __file__ 就是 getcards.py 的路徑。
# 所以路徑應該相對於 getcards.py。

# === 修改點 1: JSON 檔案路徑 ===
# 確保 JSON 檔案位於 cogs/cards/ 之下
json_filename = "閃刀姬_card_names.json"
# 獲取當前腳本 (getcards.py) 的目錄，然後拼接 'cards' 和 JSON 檔名
# os.path.dirname(__file__) 會是 'cogs' 資料夾的路徑
full_json_path = os.path.join(os.path.dirname(__file__), 'cards', json_filename)

card_names = load_card_names_map(full_json_path)

class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_challenge_states = {}
        self.user_challenge_cards = {}
        # 可以把 card_names 傳入 Cog，但如果它在全局範圍內被正確載入，直接使用也沒問題。
        # 如果你希望它成為 Cog 的一部分，可以這樣做:
        # self.card_names = card_names 

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if self.bot.user in message.mentions:
            print(f"收到訊息：{message.content} (來自 {message.author})")
            user_id = message.author.id
            content = message.content.replace(f"<@{self.bot.user.id}>", "")
            content = content.strip()

            if user_id in self.user_challenge_states and self.user_challenge_states[user_id] == "awaiting_choice":
                # 如果是選擇階段，則處理使用者輸入的數字
                chosecard = content
                if len(chosecard)==1 and chosecard.isdigit() and "1" <= chosecard <= "5":
                    the_chosen_card = int(chosecard) - 1 + random.randint(0, 4) # 隨機選擇一張卡牌
                    the_chosen_card %= 4
                    selected_card_number = self.user_challenge_cards[user_id][the_chosen_card]

                    # === 修改點 2: 圖片檔案路徑 (選擇後) ===
                    # 圖片位於 cogs/cards/ 資料夾下
                    image_path = os.path.join(os.path.dirname(__file__), 'cards', f"card{selected_card_number}.jpg")
                    
                    # 確保 card_names 字典不為空，且包含該 key
                    text = "未知卡牌" # 預設值
                    if card_names and f"card{selected_card_number}.jpg" in card_names:
                        text = card_names[f"card{selected_card_number}.jpg"]
                    else:
                        print(f"警告: 找不到卡牌名稱 '{f'card{selected_card_number}.jpg'}' 在 card_names 字典中。")


                    print(f"使用者選擇的卡牌圖片路徑：{image_path}，對應的中文名稱：{text}")
                    if not os.path.exists(image_path):
                        await message.channel.send(f"錯誤：找不到圖片檔案 `{image_path}`。請確認圖片路徑是否正確。")
                        print(f"錯誤：圖片檔案不存在於 {image_path}")
                        return

                    # 嘗試發送圖片
                    try:
                        file = discord.File(image_path, filename=f"{text}.png") # 建議使用中文名稱作為檔案名，方便區分
                        await message.channel.send(text , file=file)
                        print(f"成功發送圖片：{image_path}")
                        self.user_challenge_states[user_id] = "idle"
                        self.user_challenge_cards[user_id] = []
                        self.bot.user_status[user_id] = {"state": "idle"}  # 重置使用者狀態
                    except Exception as e:
                        await message.channel.send(f"發送圖片時發生錯誤：{e}")
                        print(f"發送圖片時發生錯誤：{e}")
                    # 重置使用者的挑戰狀態
                    self.user_challenge_states[user_id] = "idle"
                    self.user_challenge_cards[user_id] = []
                else:
                    await message.channel.send("媽的叫你輸入1~5")

            if "得卡挑戰" in message.content:
                print(f"收到得卡挑戰請求來自 {message.author}，內容：{message.content}")
                if self.bot.user_status.get(user_id)["state"] == "inmomo":
                    await message.channel.send("媽的快去射？")
                    return
                if user_id in self.user_challenge_states and self.user_challenge_states[user_id] == "awaiting_choice":
                    await message.channel.send("媽的快選")
                    return
                # 如果使用者還沒有進行挑戰，則開始新的挑戰
                cards_to_send_together = []
                self.user_challenge_states[user_id] = "awaiting_choice"
                self.bot.user_status[user_id] = "incard" # 設定使用者狀態為 "incard"
                # 隨機選擇5張卡牌
                self.user_challenge_cards[user_id] = []

                for i in range(5):
                    the_randomnumber_of_cards = random.randint(1, 27)
                    if the_randomnumber_of_cards >= 28 : # 這個判斷式是多餘的，因為 random.randint(1, 27) 不會產生 >= 28 的數字。
                        the_randomnumber_of_cards = 28 # 如果你的圖片編號最大是 28，那範圍應該是 random.randint(1, 28)
                    
                    # === 修改點 3: 圖片檔案路徑 (隨機選擇時) ===
                    image_path = os.path.join(os.path.dirname(__file__), 'cards', f"card{the_randomnumber_of_cards}.jpg")
                    self.user_challenge_cards[user_id].append(the_randomnumber_of_cards)
                    
                    # 確保 card_names 字典不為空，且包含該 key
                    card_name_display = "" # 預設為空字串
                    if card_names and f"card{the_randomnumber_of_cards}.jpg" in card_names:
                        card_name_display = card_names[f"card{the_randomnumber_of_cards}.jpg"]
                    else:
                        print(f"警告: 找不到卡牌名稱 '{f'card{the_randomnumber_of_cards}.jpg'}' 在 card_names 字典中。")
                        card_name_display = f"未知卡牌{the_randomnumber_of_cards}" # 如果找不到名稱，顯示編號


                    # 檢查圖片檔案是否存在 (這部分應該在 discord.File 之前，你原本就寫對了)
                    if not os.path.exists(image_path):
                        await message.channel.send(f"錯誤：找不到圖片檔案 `{image_path}`。請確認圖片路徑是否正確。")
                        print(f"錯誤：圖片檔案不存在於 {image_path}")
                        return # 如果缺少一張就直接返回，不發送任何圖片

                    file_obj = discord.File(image_path, filename=f"挑戰卡_{i+1}_{card_name_display}.png")
                    cards_to_send_together.append(file_obj) # <--- **將 File 物件添加到列表中**

                print(f"隨機選擇的卡牌編號：{self.user_challenge_cards[user_id]}")

                # 發送所有圖片
                if cards_to_send_together: # 只有當有圖片成功準備好時才發送
                    text = "選1~5快一點\n"
                    # 添加數字標籤到每張圖片，並顯示卡牌名稱
                    for i, card_num in enumerate(self.user_challenge_cards[user_id]):
                        display_name = ""
                        if card_names and f"card{card_num}.jpg" in card_names:
                            display_name = card_names[f"card{card_num}.jpg"]
                        else:
                            display_name = f"未知卡牌{card_num}"
                        text += f"{i+1}. {display_name}\n" # 顯示編號和卡牌名稱

                    await message.channel.send(
                        text,
                        files=cards_to_send_together # <--- **這裡將列表中的所有圖片一次性發送**
                    )
                else:
                    await message.channel.send("抱歉，未能抽到任何卡牌圖片，請稍後再試。")
            await self.bot.process_commands(message)

# Cog 檔案必須有一個 setup 函式
async def setup(bot):
    await bot.add_cog(ImageCommands(bot))