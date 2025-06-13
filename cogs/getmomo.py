import discord
from discord.ext import commands
import os # 導入 os 模組，用於處理檔案路徑
import random
from random import sample
import json



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
                    the_chosen_card = int(chosecard) - 1 + random.randint(0, 4) # 隨機選擇一張照片
                    the_chosen_card %= 4
                    
                    selected_card_number = self.user_challenge_cards[user_id][the_chosen_card]
                    image_path = f"C:\\Users\\User\\Desktop\\DC\\cogs\\momomo\\{selected_card_number}.jpg"

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
                    except Exception as e:
                        await message.channel.send(f"發送圖片時發生錯誤：{e}")
                        print(f"發送圖片時發生錯誤：{e}")
                    # 重置使用者的挑戰狀態
                    self.user_challenge_states[user_id] = "idle"
                    self.user_challenge_cards[user_id] = []
                else:
                    await message.channel.send("媽的叫你輸入1~5")
            
            if "打手槍" in message.content or "自慰" in message.content or  "漂亮寶寶" in message.content or "忍不住了" in message.content  :
                if user_id in self.user_challenge_states and self.user_challenge_states[user_id] == "awaiting_choice":
                    await message.channel.send("媽的快選")
                    return
                # 如果使用者還沒有進行挑戰，則開始新的挑戰
                cards_to_send_together = []
                self.user_challenge_states[user_id] = "awaiting_choice"
                # 隨機選擇5張卡牌
                self.user_challenge_cards[user_id] = []
                
                for i in range(5):
                   
                   
                    the_randomnumber_of_cards = random.randint(2, 21)

                    image_path = f"C:\\Users\\User\\Desktop\\DC\\cogs\\momomo\\{the_randomnumber_of_cards}.jpg"
                    self.user_challenge_cards[user_id].append(the_randomnumber_of_cards)
                    file_obj = discord.File(image_path, filename="漂亮.jpg")
                    cards_to_send_together.append(file_obj) # <--- **將 File 物件添加到列表中**

                    print(f"隨機選擇的卡牌編號：{self.user_challenge_cards[user_id]}")
                    
                    # 檢查圖片檔案是否存在
                    if not os.path.exists(image_path):
                        await message.channel.send(f"錯誤：找不到圖片檔案 `{image_path}`。請確認圖片路徑是否正確。")
                        print(f"錯誤：圖片檔案不存在於 {image_path}")
                        return
                    
                # 發送所有圖片
                if cards_to_send_together: # 只有當有圖片成功準備好時才發送
                    text = "一天一沫沫\n"
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