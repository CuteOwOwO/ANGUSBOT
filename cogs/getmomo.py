import discord
from discord.ext import commands
import os # 導入 os 模組，用於處理檔案路徑
import random
# from random import sample # 這個沒有用到，可以移除以保持程式碼整潔
import json


class momo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_challenge_states = {}
        self.user_challenge_cards = {}
        self.user_attempts = {}  

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
                    the_chosen_card = int(chosecard) - 1 + random.randint(0, 4) # 隨機選擇一張照片
                    the_chosen_card %= 4

                    selected_card_number = self.user_challenge_cards[user_id][the_chosen_card]

                    # === 修改點 1: 使用 os.path.join 構建跨平台路徑 ===
                    # __file__ 是當前腳本的路徑，os.path.dirname(__file__) 獲取腳本所在目錄 (即 cogs/)
                    # 然後拼接 momomo/ 和圖片名稱
                    image_path = os.path.join(os.path.dirname(__file__), 'momomo', f"{selected_card_number}.jpg")


                    if not os.path.exists(image_path):
                        await message.channel.send(f"錯誤：找不到圖片檔案 `{image_path}`。請確認圖片路徑是否正確。")
                        print(f"錯誤：圖片檔案不存在於 {image_path}")
                        return

                    # 嘗試發送圖片
                    try:
                        file = discord.File(image_path, filename="漂亮.png")
                        text = "不要射屏"
                        await message.channel.send(text , file=file)
                        print(f"成功發送圖片：{image_path}")
                        self.user_challenge_states[user_id] = "idle"
                        self.user_challenge_cards[user_id] = []
                        self.bot.user_status[user_id] = "0"  
                    except Exception as e:
                        await message.channel.send(f"發送圖片時發生錯誤：{e}")
                        print(f"發送圖片時發生錯誤：{e}")
                    # 重置使用者的挑戰狀態
                    self.user_challenge_states[user_id] = "idle"
                    self.user_challenge_cards[user_id] = []
                else:
                    await message.channel.send("媽的叫你輸入1~5")

            if "打手槍" in message.content or "自慰" in message.content or "漂亮寶寶" in message.content or "忍不住了" in message.content or "守羌" in message.content or "射" in message.content or "射一射" in message.content:
                print(self.bot.user_status,"status")
                if self.bot.user_status.get(user_id) == "incard":
                    await message.channel.send("先抽卡再打手槍啦")
                    return
                self.bot.user_status[user_id] = "inmomo" 
                # 如果使用者已經在進行挑戰，則提醒他們選擇
                if user_id in self.user_challenge_states and self.user_challenge_states[user_id] == "awaiting_choice":
                    await message.channel.send("媽的快選")
                    self.user_attempts[user_id] = self.user_attempts[user_id] + 1
                    # 如果使用者已經射了3次，則結束挑戰並發送獎勵
                    if self.user_attempts[user_id] >= 3:
                        file = discord.File(os.path.join(os.path.dirname(__file__), 'momomo', '1.jpg'), filename="fail.jpg")
                        await message.channel.send("媽的你已經射太多次了，這是你的獎勵", file=file)
                        self.user_challenge_states[user_id] = "idle"
                        self.user_challenge_cards[user_id] = []
                        self.user_attempts[user_id] = 0
                        self.bot.user_status[user_id] = "0"  
                    return
                # 如果使用者還沒有進行挑戰，則開始新的挑戰
                cards_to_send_together = []
                self.user_challenge_states[user_id] = "awaiting_choice"
                # 隨機選擇5張卡牌
                self.user_challenge_cards[user_id] = []

                for i in range(5):
                    the_randomnumber_of_cards = random.randint(1,68)
                    if the_randomnumber_of_cards ==41 :
                        the_randomnumber_of_cards = 42

                    # === 修改點 2: 使用 os.path.join 構建跨平台路徑 ===
                    image_path = os.path.join(os.path.dirname(__file__), 'momomo', f"{the_randomnumber_of_cards}.jpg")

                    self.user_challenge_cards[user_id].append(the_randomnumber_of_cards)

                    # 檢查圖片檔案是否存在 (這部分應該在 discord.File 之前，你原本就寫對了)
                    if not os.path.exists(image_path):
                        await message.channel.send(f"錯誤：找不到圖片檔案 `{image_path}`。請確認圖片路徑是否正確。")
                        print(f"錯誤：圖片檔案不存在於 {image_path}")
                        # 這裡可以考慮 break 或 continue，或者處理缺少檔案的情況
                        # 如果是關鍵功能，可能需要在這裡返回或終止，避免發送不完整的圖片集
                        return # 如果缺少一張就直接返回，不發送任何圖片

                    file_obj = discord.File(image_path, filename=f"漂亮_{i+1}.jpg") # 更改 filename 避免所有圖片都叫 "漂亮.jpg"
                    cards_to_send_together.append(file_obj) # <--- **將 File 物件添加到列表中**

                print(f"隨機選擇的卡牌編號：{self.user_challenge_cards[user_id]}") # 這會印出所有選中的卡牌編號列表

                # 發送所有圖片
                if cards_to_send_together: # 只有當有圖片成功準備好時才發送
                    text = "一天一沫沫\n"
                    # 添加數字標籤到每張圖片
                    text = "快選1~5,趕快射一射" # 提示用戶選擇

                    await message.channel.send(
                        text,
                        files=cards_to_send_together # <--- **這裡將列表中的所有圖片一次性發送**
                    )
                else:
                    await message.channel.send("抱歉，未能抽到任何卡牌圖片，請稍後再試。")
                await self.bot.process_commands(message)


# Cog 檔案必須有一個 setup 函式
'''async def setup(bot):
    await bot.add_cog(momo(bot))'''