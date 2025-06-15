import discord
from discord.ext import commands
import os # 導入 os 模組，用於處理檔案路徑
import random
# from random import sample # 這個沒有用到，可以移除以保持程式碼整潔
import json


class sendselectedmomo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.PACK_FOLDER_PREFIX = "momomo" 
        
    async def start_initial_draw(self, user_id: int, channel: discord.TextChannel):
        current_user_status_info = self.bot.user_status.get(user_id, {"state": "idle"})
        
        # 再次確認狀態，以防萬一
        if not (current_user_status_info["state"] == "folder_selected" and 
                "selected_folder_number" in current_user_status_info):
            # 如果狀態不正確，則發送錯誤訊息並重置狀態
            print(f"錯誤: 用戶 {user_id} 狀態不正確 ({current_user_status_info.get('state')})，無法啟動初始抽卡。")
            await channel.send("抱歉，您的卡包選擇狀態有誤，請重新開始。")
            self.bot.user_status[user_id] = {"state": "idle"}
            return
        
        selected_folder_number = current_user_status_info["selected_folder_number"]
        selected_folder_name = current_user_status_info["selected_folder_name"]
        self.bot.user_status[user_id]["displayed_cards"] = [] # 用於儲存這 5 張卡牌的檔名
        file_to_send = []
        
        BASE_CARDS_DIR = os.path.join(os.path.dirname(__file__), f"{self.PACK_FOLDER_PREFIX}{selected_folder_number}")
        all_card_files_in_folder = [f for f in os.listdir(BASE_CARDS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        numberofcrds = len(all_card_files_in_folder)
        
        for i in range(5):
            the_chosen_card = random.randint(1, numberofcrds)
            self.bot.user_status[user_id]["displayed_cards"].append(the_chosen_card)
        print(f"用戶 {user_id} 的初始抽卡已完成，顯示的卡牌編號為：{self.bot.user_status[user_id]['displayed_cards']}")
        
        for i in self.bot.user_status[user_id]["displayed_cards"]:
            image_path = os.path.join(BASE_CARDS_DIR, f"{i}.jpg")
            if not os.path.exists(image_path):
                await channel.send(f"錯誤：找不到圖片檔案 `{image_path}`。請確認圖片路徑是否正確。")
                print(f"錯誤：圖片檔案不存在於 {image_path}")
                return
            
            file_obj = discord.File(image_path, filename=f"漂亮_{i}.jpg")
            file_to_send.append(file_obj) # 將 File 物件添加到列表中
        if file_to_send:
            text = f"你選擇：**{selected_folder_name}**\n請選擇1~5號卡牌進行禁慾挑戰！"
            await channel.send(
                text,
                files=file_to_send # 將列表中的所有圖片一次性發送
            )
            self.bot.user_status[user_id]["state"] = "awaiting_final_pick"
            print(f"用戶 {user_id} 狀態更新為 awaiting_final_pick。")
        else:
            await channel.send(f"抱歉，未能從 **{self.PACK_FOLDER_PREFIX}{selected_folder_number}** 中抽到任何卡牌圖片。", )
            self.bot.user_status[user_id]["state"] = "idle" 
       


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if self.bot.user in message.mentions:
            print(f"我我我我我收到訊息：{message.content} (來自 {message.author})")
            user_id = message.author.id
            content = message.content.replace(f"<@{self.bot.user.id}>", "")
            content = content.strip()
            print("在抽卡階段收到訊息了!!")
            if self.bot.user_status[user_id].get("state") == "awaiting_final_pick":
                print(f"用戶 {user_id} 正在等待最終選擇階段。")
                # 如果是選擇階段，則處理使用者輸入的數字
                chosecard = content
                if len(chosecard)==1 and chosecard.isdigit() and "1" <= chosecard <= "5":
                    the_chosen_card = int(chosecard) - 1 + random.randint(0, 4) # 隨機選擇一張照片
                    the_chosen_card %= 4

                    current_user_status_info = self.bot.user_status.get(user_id, {"state": "idle"})
                    selected_card_number = self.bot.user_status[user_id]["displayed_cards"][the_chosen_card]
                    selected_folder_number = current_user_status_info.get("selected_folder_number", None)
                    BASE_CARDS_DIR = os.path.join(os.path.dirname(__file__), f"{self.PACK_FOLDER_PREFIX}{selected_folder_number}")
                    image_path = os.path.join(BASE_CARDS_DIR, f"{selected_card_number}.jpg")


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
                        print(self.bot.user_status[user_id]["message_id"])
                        # 刪除之前的卡包選擇訊息
                        channel = message.channel
                        if "message_id" in self.bot.user_status[user_id]:
                            try:
                                # 獲取原始訊息物件
                                folder_selection_message = await channel.fetch_message(current_user_status_info["message_id"])
                                await folder_selection_message.delete()
                                print(f"已刪除卡包選擇訊息 ID: {current_user_status_info['message_id']}")
                            except discord.NotFound:
                                print(f"嘗試刪除卡包選擇訊息 {current_user_status_info['message_id']} 但未找到。")
                            except discord.Forbidden:
                                print(f"機器人沒有權限刪除卡包選擇訊息 {current_user_status_info['message_id']}。")
                            except Exception as e:
                                print(f"刪除卡包選擇訊息時發生錯誤: {e}")
                                
                        self.bot.user_status[user_id]["state"] = "idle"  # 重置使用者狀態
                        self.bot.user_status[user_id]["display"] = []
                                
                                
                                
                    except Exception as e:
                        await message.channel.send(f"發送圖片時發生錯誤：{e}")
                        print(f"發送圖片時發生錯誤：{e}")
                        # 重置使用者的挑戰狀態
                    self.bot.user_status[user_id]["state"] = "idle"
                    self.bot.user_status[user_id]["display"] = []
                else:
                    await message.channel.send("媽的叫你輸入1~5")


# Cog 檔案必須有一個 setup 函式
async def setup(bot):
    await bot.add_cog(sendselectedmomo(bot))