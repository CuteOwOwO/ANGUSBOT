import discord
from discord.ext import commands
import os
import random
import json

# --- 1. 定義載入 JSON 的函數 (保持不變) ---
def load_momofolder_name(json_file_path):
    if not os.path.exists(json_file_path):
        print(f"錯誤: JSON 檔案 '{json_file_path}' 不存在。")
        return {}
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

json_filename = "momoname.json"
full_json_path = os.path.join(os.path.dirname(__file__),  json_filename)
momofoldernames = load_momofolder_name(full_json_path)

class sendfolder(commands.Cog): # 建議改名，更具描述性
    def __init__(self, bot):
        self.bot = bot
        # 定義卡包資料夾的路徑
        self.BASE_PACKS_DIR = os.path.dirname(__file__) 
        self.PACK_FOLDERS_PREFIX = "momomo" # 資料夾前綴
        self.NUM_PACK_FOLDERS = 5 # 總共有多少個 momo 資料夾 (momo1, momo2, ..., momo5)
        self.EMOJI_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        self.TRIGGER_KEYWORDS = ["選卡包", "打手槍", "自慰", "漂亮寶寶", "忍不住了", "守羌", "射", "射一射"]
        

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        user_id = message.author.id
        cleaned_content = message.clean_content.strip()
        
        if user_id not in self.bot.user_status:
            self.bot.user_status[user_id] = {"state": "idle"}

        # 檢查是否標註了機器人並且包含觸發關鍵詞
        if self.bot.user in message.mentions and any(keyword in cleaned_content for keyword in self.TRIGGER_KEYWORDS):
            
            
            current_user_state_info = self.bot.user_status.get(user_id, {"state": "idle"})
            
            # 如果使用者正在進行任何非 "idle" 的互動，則提示並返回
            if current_user_state_info["state"] != "idle":
                # 更精確的判斷和提示
                if current_user_state_info["state"] == "waiting_chose_folder":
                    await message.channel.send("你還在選寫真集，按表符啦白癡。", reference=message)
                elif current_user_state_info["state"] == "folder_selected": # 已選擇卡包，但還沒抽卡
                    await message.channel.send("快點選圖片。", reference=message)
                elif current_user_state_info["state"] == "drawing_card": # 正在抽卡
                     await message.channel.send("你目前正在選圖片中，請先完成！", reference=message)
                elif current_user_state_info["state"] == "awaiting_final_pick": # 最終選擇階段
                    await message.channel.send("你目前正在等待最終選擇階段，請輸入1~5選擇卡牌。", reference=message)
                else: # 其他未預期的狀態
                    await message.channel.send("你目前正在進行其他操作，請稍後再嘗試。", reference=message)
                return 

            # --- 開始新的卡包選擇流程 ---
            print(f"User {user_id} triggered folder selection.")
            
            cards_to_send_together = []
            the_chosen_folder_numbers = [] # 儲存本次隨機選擇的資料夾編號，用於後續處理和狀態保存
            

            # 隨機選擇5個不同的資料夾編號作為展示
            possible_folder_nums = list(range(1, self.NUM_PACK_FOLDERS + 1)) # 例如 [1, 2, 3, 4, 5]
            if len(possible_folder_nums) < 5: # 如果可用的卡包少於5個，則隨機選擇，允許重複
                the_chosen_folder_numbers = [random.choice(possible_folder_nums) for _ in range(5)]
            else: # 如果足夠，則隨機選擇5個不重複的
                the_chosen_folder_numbers = random.sample(possible_folder_nums, 5)
            
            

            for i, folder_num in enumerate(the_chosen_folder_numbers):
                # 構建資料夾路徑和圖片路徑    
                folder_path = os.path.join(self.BASE_PACKS_DIR, f"{self.PACK_FOLDERS_PREFIX}{folder_num}")
                all_images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                random_image_filename = random.choice(all_images)
                image_path = os.path.join(folder_path, random_image_filename)

                if not self.bot.chosen_folder_names.get(user_id):
                    self.bot.chosen_folder_names[user_id] = []
                self.bot.chosen_folder_names[user_id].append(momofoldernames.get(str(folder_num), f"未知資料夾{folder_num}")) # 獲取中文名稱，若無則使用預設值

                if not os.path.isdir(folder_path):
                    print(f"警告：找不到卡包資料夾 '{folder_path}'。")
                    continue # 跳過不存在的資料夾

                if not os.path.exists(image_path):
                    print(f"警告：資料夾 '{folder_path}' 中找不到代表圖片 '{image_path}'。")
                    continue # 跳過沒有代表圖的資料夾

                try:
                    file_obj = discord.File(image_path, filename=f"{self.PACK_FOLDERS_PREFIX}{folder_num}_代表圖.jpg")
                    cards_to_send_together.append(file_obj)
                except Exception as e:
                    print(f"準備卡包代表圖 '{image_path}' 時發生錯誤: {e}")
                    continue

            if not cards_to_send_together: # 如果沒有任何圖片成功準備
                await message.channel.send("抱歉，未能準備任何卡包代表圖片，請檢查資料夾配置。", reference=message)
                self.bot.user_status[user_id] = {"state": "idle"} # 重置狀態
                await self.bot.process_commands(message)
                return

            # --- 組合文字訊息 ---
            text_lines = ["請點擊下方表情符號選擇一個卡包："]
            for idx, folder_num in enumerate(the_chosen_folder_numbers):
                folder_name_cn = momofoldernames.get(str(folder_num), f"未知資料夾{folder_num}")
                text_lines.append(f"{self.EMOJI_NUMBERS[idx]} {folder_name_cn}") # 使用表情符號作為列表前綴
            
            text_message = "\n".join(text_lines)

            # --- 發送訊息並添加反應 ---
            selection_message = await message.channel.send(
                text_message,
                files=cards_to_send_together,
                reference=message # 回覆到觸發訊息
            )
            
            # --- 更新 bot.user_status ---
            # 儲存本次發送的訊息 ID 和卡包順序，供 ReactionHandlerCog 監聽
            self.bot.user_status[user_id]["state"] = "waiting_chose_folder" # 更新狀態為等待選擇資料夾
            self.bot.user_status[user_id]["message_channel_id"] = message.channel.id
            self.bot.user_status[user_id]["message_id"] = selection_message.id
            self.bot.user_status[user_id]["chosen_folders_order"] = the_chosen_folder_numbers # 儲存本次展示的資料夾編號順序
            self.bot.user_status[user_id]["last_message_id"] = selection_message.id
            print("this is the message_id", self.bot.user_status[user_id]["message_id"])

            # 添加表情符號
            # 只為實際發送的卡包數量添加表情符號
            for i in range(len(cards_to_send_together)): 
                # 確保表情符號索引不超過 EMOJI_NUMBERS 的範圍
                if i < len(self.EMOJI_NUMBERS):
                    await selection_message.add_reaction(self.EMOJI_NUMBERS[i])
                else:
                    print(f"警告: 表情符號數量不足以匹配所有卡包代表圖。")
            
            print(f"發送卡包選擇訊息給 {self.bot.user.display_name}，等待反應。狀態: {self.bot.user_status[user_id]}")

        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(sendfolder(bot))