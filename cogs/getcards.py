import discord
from discord.ext import commands
import os # 導入 os 模組，用於處理檔案路徑
import random
from random import sample
import json

flag = 0
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
            # json.load(f) 會直接將 JSON 內容轉換為 Python 字典
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
# 假設你的 JSON 檔案位於 'ourocg_cards_numbered' 子資料夾中
# 你需要根據你的實際情況調整這個路徑
json_dir = "C:\\Users\\User\\Desktop\\DC\\cogs\\cards"  
json_filename = "閃刀姬_card_names.json" # 確保這個檔名和爬蟲產生的相符
full_json_path = os.path.join(json_dir, json_filename)

# 將載入的字典命名為 card_names，就像 C++ 的 map
card_names = load_card_names_map(full_json_path)

class ImageCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_challenge_states = {} 
        self.user_challenge_cards = {} 

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
                    image_path = f"C:\\Users\\User\\Desktop\\DC\\cogs\\cards\\card{selected_card_number}.jpg"
                    text = card_names[(f"card{selected_card_number}.jpg")]
                    
                    print(f"使用者選擇的卡牌圖片路徑：{image_path}，對應的中文名稱：{text}")
                    if not os.path.exists(image_path):
                        await message.channel.send(f"錯誤：找不到圖片檔案 `{image_path}`。請確認圖片路徑是否正確。")
                        print(f"錯誤：圖片檔案不存在於 {image_path}")
                        return
                    
                    # 嘗試發送圖片
                    try:
                        file = discord.File(image_path, filename="你選到的卡.png")
                        
                        await message.channel.send(text , file=file)
                        print(f"成功發送圖片：{image_path}")
                        self.user_challenge_states[user_id] = "idle"
                        self.user_challenge_cards[user_id] = []
                    except Exception as e:
                        await message.channel.send(f"發送圖片時發生錯誤：{e}")
                        print(f"發送圖片時發生錯誤：{e}")
                    # 重置使用者的挑戰狀態
                    self.user_challenge_states[user_id] = "idle"
                    self.user_challenge_cards[user_id] = []
                else:
                    await message.channel.send("媽的叫你輸入1~5")
            
            if "得卡挑戰" in message.content:
                if user_id in self.user_challenge_states and self.user_challenge_states[user_id] == "awaiting_choice":
                    await message.channel.send("媽的快選")
                    return
                # 如果使用者還沒有進行挑戰，則開始新的挑戰
                cards_to_send_together = []
                self.user_challenge_states[user_id] = "awaiting_choice"
                # 隨機選擇5張卡牌
                self.user_challenge_cards[user_id] = []
                
                for i in range(5):
                   
                   
                    the_randomnumber_of_cards = random.randint(1, 27)
                    if the_randomnumber_of_cards >= 28 :
                        the_randomnumber_of_cards = 28
                    
                    image_path = f"C:\\Users\\User\\Desktop\\DC\\cogs\\cards\\card{the_randomnumber_of_cards}.jpg"
                    self.user_challenge_cards[user_id].append(the_randomnumber_of_cards)
                    file_obj = discord.File(image_path, filename=f"挑戰卡_{i+1}_{card_names[f'card{the_randomnumber_of_cards}.jpg']}.png")
                    cards_to_send_together.append(file_obj) # <--- **將 File 物件添加到列表中**

                    print(f"隨機選擇的卡牌編號：{self.user_challenge_cards[user_id]}")
                    
                    # 檢查圖片檔案是否存在
                    if not os.path.exists(image_path):
                        await message.channel.send(f"錯誤：找不到圖片檔案 `{image_path}`。請確認圖片路徑是否正確。")
                        print(f"錯誤：圖片檔案不存在於 {image_path}")
                        return
                    
                # 發送所有圖片
                if cards_to_send_together: # 只有當有圖片成功準備好時才發送
                    text = "選1~5快一點\n"
                    await message.channel.send(
                        text,   
                        files=cards_to_send_together # <--- **這裡將列表中的所有圖片一次性發送**
                    )
                else:
                    await message.channel.send("抱歉，未能抽到任何卡牌圖片，請稍後再試。")
                await self.bot.process_commands(message)

# Cog 檔案必須有一個 setup 函式
'''async def setup(bot):
    await bot.add_cog(ImageCommands(bot))'''