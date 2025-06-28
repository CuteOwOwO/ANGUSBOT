import discord
from discord.ext import commands
import os
import google.generativeai as genai
import json 
from dotenv import load_dotenv
import asyncio # 匯入 asyncio 模組
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import logging # <-- 確保有導入 logging
from . import image_generator
from io import BytesIO # 用於將圖片數據發送給 Discord
load_dotenv()

# 從環境變數中獲取 Gemini API 金鑰
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")

# 配置 Gemini API (在 Cog 初始化時執行)
if GEMINI_API_KEY: #
    genai.configure(api_key=GEMINI_API_KEY) #
else:
    print("警告: 未找到 GEMINI_API_KEY 環境變數。Gemini AI 功能將無法使用。")
    
if GEMINI_API_KEY_2: #
    genai.configure(api_key=GEMINI_API_KEY_2) #
else:
    print("警告: 未找到 GEMINI_API_KEY_2 環境變數。Gemini AI 功能將無法使用。")

GENERATION_CONFIG = {
    "temperature": 1.7,
    "max_output_tokens": 1500,
    "top_p": 0.95,
    "top_k": 256,
}

def load_json_prompt_history(file_name):
    current_dir = os.path.dirname(__file__)
    prompt_file_path = os.path.join(current_dir, 'prompts', file_name)
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            return json.load(f) # 使用 json.load()
    except FileNotFoundError:
        print(f"錯誤: JSON 提示檔案 '{prompt_file_path}' 未找到。請確保檔案存在。")
        # 返回一個默認或空的歷史，防止程式崩潰
        return [
            {"role": "user", "parts": ["你是一位樂於助人的 Discord 機器人，用友善、簡潔的方式回答使用者的問題。"]},
            {"role": "model", "parts": ["好的，我明白了，我將會用友善、簡潔的方式回答使用者的問題。"]}
        ]
    except json.JSONDecodeError as e:
        print(f"錯誤: 解析 JSON 提示檔案 '{prompt_file_path}' 失敗: {e}")
        return [
            {"role": "user", "parts": ["你是一位樂於助人的 Discord 機器人，用友善、簡潔的方式回答使用者的問題。"]},
            {"role": "model", "parts": ["好的，我明白了，我將會用友善、簡潔的方式回答使用者的問題。"]}
        ]
    except Exception as e:
        print(f"讀取 JSON 提示檔案 '{prompt_file_path}' 時發生未知錯誤: {e}")
        return [
            {"role": "user", "parts": ["你是一位樂於助人的 Discord 機器人，用友善、簡潔的方式回答使用者的問題。"]},
            {"role": "model", "parts": ["好的，我明白了，我將會用友善、簡潔的方式回答使用者的問題。"]}
        ]
        

USER_ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__),  'achievements', 'user_achievements.json')
CONVERSATION_RECORDS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'conversation_records.json')

async def save_user_achievements_local(data, file_path):
    """將使用者成就記錄保存到 JSON 檔案。在單獨的線程中執行阻塞的 I/O 操作。"""
    await asyncio.to_thread(_save_user_achievements_sync_local, data, file_path)

def _save_user_achievements_sync_local(data, file_path):
    """實際執行檔案保存的同步函數，供 asyncio.to_thread 調用。"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"使用者成就記錄已保存到 '{file_path}'。")
    except Exception as e:
        print(f"保存使用者成就記錄到 '{file_path}' 時發生錯誤: {e}")
# --- 保存邏輯結束 ---

async def save_conversation_data_local(data, file_path):
    """將對話紀錄保存到 JSON 檔案。在單獨的線程中執行阻塞的 I/O 操作。"""
    await asyncio.to_thread(_save_conversation_sync_local, data, file_path)

def _save_conversation_sync_local(data, file_path):
    """實際執行對話紀錄檔案保存的同步函數，供 asyncio.to_thread 調用。"""
    try:
        # 確保資料夾存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[mention Cog] 對話紀錄已保存到 '{file_path}'。")
        logging.info(f"[mention Cog] 對話紀錄已保存到 '{file_path}'。") # 增加日誌記錄
    except Exception as e:
        print(f"[mention Cog] 保存對話紀錄到 '{file_path}' 時發生錯誤: {e}")
        logging.error(f"[mention Cog] 保存對話紀錄到 '{file_path}' 時發生錯誤: {e}", exc_info=True) # 增加錯誤日誌記錄


class MentionResponses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TRIGGER_KEYWORDS = ["選卡包", "打手槍", "自慰", "漂亮寶寶", "忍不住了", "守羌", "射", "射一射","得卡","天氣","出門","氣溫","猜病"]
        self.dont_reply_status = ["waiting_chose_folder","drawing_card","awaiting_final_pick","guessing"]
        self.user_chats = {} 
        
        # 初始化 Gemini 模型
        # 這裡根據你的需求選擇模型，例如 'gemini-pro'
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-1.5-flash-latest') # <-- 在這裡初始化 self.model
                print("[MentionResponses Cog] Gemini API configured and model initialized successfully!")
            except Exception as e:
                print(f"[MentionResponses Cog] Error configuring Gemini API or initializing model: {e}")
                print("請檢查您的 GEMINI_API_KEY 是否正確。MentionResponses 的 Gemini 功能將被禁用。")
                self.model = None # 設定為 None 表示模型不可用
        else:
            print("[MentionResponses Cog] GEMINI_API_KEY not found in .env file. MentionResponses 的 Gemini 功能將被禁用。")
            self.model = None # 設定為 None 表示模型不可用

    # 監聽 on_message 事件
    @commands.Cog.listener()
    async def on_message(self, message):
        # 排除機器人本身的訊息，避免無限循環
        if message.author == self.bot.user:
            return
        #print("this is the right version of mention2.py") # Debug: 確認是否正確載入
        # 【新加】先檢查訊息是否為指令，如果是指令，直接返回
        # 這可以避免重複處理指令，並確保 on_message 只處理非指令的 mention 訊息
        ctx = await self.bot.get_context(message)
        if ctx.command:
            return

        content = message.content.replace(f"<@{self.bot.user.id}>", "")
        content = content.strip()

        # 檢查訊息是否包含機器人的標註
        # 並且不包含觸發卡包選擇的關鍵詞
        user_id = message.author.id
        user_id_str = str(user_id)  # 將 user_id 轉換為字串，以便用於字典鍵
        if user_id_str not in self.bot.conversation_histories_data:
            self.bot.conversation_histories_data[user_id_str] = {
                "current_mode": "loli", # 預設為蘿莉模式
                "modes": {
                    "loli": [],
                    "sexy": []
                }
            }
            await save_conversation_data_local(self.bot.conversation_histories_data, CONVERSATION_RECORDS_FILE)
            logging.info(f"[mention Cog] 為新使用者 {user_id_str} 初始化對話紀錄結構。")
        
        
        current_mode_data = self.bot.conversation_histories_data[user_id_str]
        # 如果 modes 字典中缺少 'loli' 或 'sexy' 模式的列表，也進行初始化 (以防舊數據格式不完整)
        if "loli" not in current_mode_data["modes"]:
            current_mode_data["modes"]["loli"] = []
        if "sexy" not in current_mode_data["modes"]:
            current_mode_data["modes"]["sexy"] = []

        user_current_mode = self.bot.user_which_talkingmode.get(user_id, current_mode_data.get("current_mode", "loli"))
        self.bot.user_which_talkingmode[user_id] = user_current_mode # 同步到即時狀態
        current_mode_data["current_mode"] = user_current_mode # 同步到持久化數據
        
        
        if user_id not in self.bot.user_status or not isinstance(self.bot.user_status[user_id], dict):
                self.bot.user_status[user_id] = {"state": "idle"}
        
        for i in self.dont_reply_status:
            if self.bot.user_status[user_id]["state"] == (i):
                print(f"[GeminiAI Cog] 使用者 {user_id} 當前狀態為 {self.bot.user_status[user_id]['state']}，不回應。")
                return
        if len(content) == 1:
            return 
        if self.bot.user in message.mentions and not any(keyword in content for keyword in self.TRIGGER_KEYWORDS):
            
            if "變成御姊" in content or "御姐" in content or "御姊" in content:
                async with message.channel.typing():
                    if user_id in self.bot.user_chats:
                        del self.bot.user_chats[user_id] # 清除舊的會話記憶
                        dynamic_system_prompt = load_json_prompt_history('sexy.json') # 使用 sexy.json 作為系統提示
                        self.bot.user_chats[user_id] = self.model.start_chat(history=dynamic_system_prompt)
                        
                self.bot.user_which_talkingmode[user_id] = "sexy" # 記錄使用者當前模式為 sexy
                print(f"[mention Cog] 使用者 {user_id} 變成{self.bot.user_which_talkingmode[user_id]}mode。")
                        
            if "變成蘿莉" in content or "蘿莉" in content:
                async with message.channel.typing():
                    if user_id in self.bot.user_chats:
                        del self.bot.user_chats[user_id] # 清除舊的會話記憶
                        dynamic_system_prompt = load_json_prompt_history('mention2.json') 
                        self.bot.user_chats[user_id] = self.model.start_chat(history=dynamic_system_prompt)
                self.bot.user_which_talkingmode[user_id] = "loli" # 記錄使用者當前模式為 loli

            # 【新加】確保 user_id 存在於 self.bot.user_status
            user_id = message.author.id
            if user_id not in self.bot.user_status or not isinstance(self.bot.user_status[user_id], dict):
                self.bot.user_status[user_id] = {"state": "idle"}

            try:
                # 簡單的長度檢查，避免發送過長的問題給 API
                if len(content) > 200:
                    await message.channel.send("問題太長了，請簡短一些。",reference = message)
                    return

                # 檢查 self.model 是否已初始化
                if not self.model: #
                    await message.channel.send("Gemini AI 服務未啟用，請檢查 API 金鑰。")
                    return

                # 使用 generate_content 呼叫 Gemini API
                
                if user_id not in self.bot.user_chats:
                    # 如果是新用戶或該用戶的聊天會話尚未開始，則使用系統提示初始化一個新的聊天會話
                    print(f"為使用者 {user_id} 初始化新的 Gemini 聊天會話，載入系統提示。")
                    dynamic_system_prompt = load_json_prompt_history('normal.json') # 使用預設的系統提示
                    
                    self.bot.user_which_talkingmode[user_id] = "loli" # 記錄使用者當前模式為 loli
                    print(f"!![mention Cog] 使用者 {user_id} 變成{self.bot.user_which_talkingmode[user_id]}模式。")
                    print(f"[mention Cog] 為使用者 {user_id} 初始化新的 loli 聊天會話。")
                    

                    self.bot.user_chats[user_id] = self.model.start_chat(history=dynamic_system_prompt)
                    
                #print("user chats", self.bot.user_chats) #
                chat = self.bot.user_chats[user_id] # 獲取該使用者的聊天會話物件
                #print(self.bot.user_chats[user_id], "user chat") #
                if self.bot.user_which_talkingmode.get(user_id) == "sexy":
                    content = content + "(你是一隻高冷性感的御姊女性貓咪)"
                elif self.bot.user_which_talkingmode.get(user_id) == "loli":
                    content = content + "(你是一隻可愛的蘿莉貓咪)"

                response = chat.send_message(content)
                #response = self.model.generate_content(content) #

                # 檢查是否有內容並傳送回 Discord
                if response and response.text:
                    
            
                    # Discord 訊息長度限制為 2000 字元
                    if len(response.text) > 2000:
                        await message.channel.send("答案太長了，將分段發送：")
                        # 將答案分割成多條訊息，每條不超過 1990 字元 (留一些空間給 ``` 和標點)
                        chunks = [response.text[i:i+1990] for i in range(0, len(response.text), 1990)]
                        for chunk in chunks:
                            await message.channel.send(f"```{chunk}```") # 使用 Markdown 程式碼區塊格式化
                    else:
                        await message.channel.send(f"```{response.text}```", reference = message) # 使用 Markdown 程式碼區塊格式化
                        print(f"[GeminiAI Cog] 回答成功發送：{response.text[:50]}...") # 日誌前50個字元

                    # 更新最後處理的訊息 ID，與使用者相關聯
                    self.bot.user_status[user_id]["last_message_id"] = message.id
                    
                    #儲存對話歷史
                    try:
                        if user_id_str in self.bot.user_chats:
                            print(f"{user_id_str} 成功提取歷史") # Debug: 檢查提取的歷史是否正確
                            active_chat_session = self.bot.user_chats[user_id_str]

                            # 從當前活躍的 Gemini 聊天會話中異步提取歷史
                            current_chat_history = []
                            async for message_item in active_chat_session.history: # 這裡是關鍵，從 chat.history() 異步獲取
                                # 將每個 Message 物件轉換為字典格式，確保只包含 'role' 和 'parts'
                                if hasattr(message_item, '_as_dict'):
                                    processed_item = message_item._as_dict()
                                    # 再次確保 parts 內部是 {'text': '...'} 格式，且移除空字串
                                    if 'parts' in processed_item and isinstance(processed_item['parts'], list):
                                        valid_parts = []
                                        for part in processed_item['parts']:
                                            if isinstance(part, dict) and 'text' in part and part['text'] and part['text'].strip():
                                                valid_parts.append({"text": part['text'].strip()})
                                            elif isinstance(part, str) and part.strip(): # 處理 parts 元素直接是字串的情況
                                                valid_parts.append({"text": part.strip()})
                                        processed_item['parts'] = valid_parts
                                        if valid_parts: # 只有parts不為空才加入
                                            current_chat_history.append(processed_item)
                                else:
                                    logging.warning(f"[mention Cog] 歷史項目格式不符，跳過: {message_item}")

                            # 將提取到的歷史保存到該用戶當前模式的歷史列表中
                            # 確保 self.bot.conversation_histories_data[user_id_str]["modes"][user_current_mode] 存在
                            if user_current_mode not in self.bot.conversation_histories_data[user_id_str]["modes"]:
                                self.bot.conversation_histories_data[user_id_str]["modes"][user_current_mode] = []

                            self.bot.conversation_histories_data[user_id_str]["modes"][user_current_mode] = current_chat_history

                            # 呼叫我們剛剛在 mention2.py 內新增的通用保存函數來持久化數據
                            # 注意這裡不再需要從 main 導入，因為函數就在這個檔案內
                            await save_conversation_data_local(self.bot.conversation_histories_data, CONVERSATION_RECORDS_FILE)
                        # --- 結束新增區塊 ---
                            logging.info(f"[mention Cog] 使用者 {user_id_str} 在 '{user_current_mode}' 模式下的對話歷史已保存。")

                    except Exception as e:
                        logging.error(f"[mention Cog] 保存對話歷史時發生錯誤: {e}")

                    print("alive here")
                    #成就系統
                    try:
                        if hasattr(self.bot, 'loli_achievements_definitions') and \
                           hasattr(self.bot, 'sexy_achievements_definitions') and \
                           hasattr(self.bot, 'user_achievements') and \
                           hasattr(self.bot, 'user_which_talkingmode'):
                            # 確保使用者有成就記錄，如果沒有則初始化為空列表
                            user_id = str(message.author.id)
                            print(f"[mention Cog] 檢查使用者 {user_id} 的成就...")
                            user_current_mode = self.bot.user_which_talkingmode[message.author.id] # 獲取使用者模式，預設為蘿莉版
                            print(f"[mention Cog] 使用者 {user_id} 當前模式為：{user_current_mode}")
                            achievements_to_check = []
                            
                            if user_current_mode == "sexy":
                                achievements_to_check = self.bot.sexy_achievements_definitions
                                print(f"[mention Cog] 檢查御姊版成就 (使用者: {user_id})")
                            else: # 預設或 "loli" 模式
                                achievements_to_check = self.bot.loli_achievements_definitions
                                print(f"[mention Cog] 檢查蘿莉版成就 (使用者: {user_id})")
                            #print(f"[mention Cog] 成就資料: {self.bot.achievements_data}")
                            if user_id not in self.bot.user_achievements:
                                self.bot.user_achievements[user_id] = {}
                                self.bot.user_achievements[user_id]['total_achievement_count'] = 0
                                
                            #print(achievements_to_check, "成就資料") # Debug: 檢查成就資料是否正確

                            for achievement in achievements_to_check:
                                achievement_name = achievement.get("name")
                                # 檢查該成就是否已被使用者解鎖
                               
                                    # 檢查模型回覆是否包含任何觸發短語
                                for phrase in achievement.get("trigger_phrases", []):
                                    if isinstance(response.text, str) and phrase.lower() in response.text.lower():
                                            
                                        current_count = self.bot.user_achievements[user_id].get(achievement_name, 0)
                                        self.bot.user_achievements[user_id][achievement_name] = current_count + 1 # <--- 將 append 改為增加次數
                                        print( f"[mention Cog] 使用者 {user_id} 解鎖成就：{achievement_name}，目前次數：{current_count + 1}")
                                        
                                        self.bot.user_achievements[user_id]['total_achievement_count'] = self.bot.user_achievements[user_id].get('total_achievement_count', 0) + 1
                                        print(f"[mention Cog] 使用者 {user_id} 總成就次數增加到 {self.bot.user_achievements[user_id]['total_achievement_count']}")
                                        
                                        add_text = ""
                                        if current_count == 0: # 第一次解鎖
                                            print(f"[mention Cog] 使用者 {user_id} 第一次解鎖成就：{achievement_name}")
                                            add_text = "貓咪剛認識你"
                                            congratulatory_message = achievement.get("unlock_message", f"🎉 恭喜！你的成就 **《{achievement_name}》** 已經解鎖！")
                                        elif current_count == 4:
                                            add_text = "貓咪開始喜歡你了"
                                            congratulatory_message = f"🥉 恭喜！你的成就 **《{achievement_name}》** 已經解鎖 **5** 次，獲得 **銅級** 獎章！繼續努力！"
                                        elif current_count == 29:
                                            add_text = "貓咪對你有好感了"
                                            congratulatory_message = f"🥈 驚喜！你的成就 **《{achievement_name}》** 已經解鎖 **30** 次，達到 **銀級** 獎章！你真棒！"
                                        elif current_count == 99: # 你可以設定更高的等級，例如金級
                                            add_text = "貓咪愛上你了，可以適當增加居家風格及減少角色衣著"
                                            congratulatory_message = f"🏆 太厲害了！你的成就 **《{achievement_name}》** 已經解鎖 **100** 次，榮獲 **金級** 獎章！無人能及！"
                                        else:
                                            congratulatory_message = None
                                        if congratulatory_message:
                                            await message.channel.send(congratulatory_message, reference=message)
                                            print(f"[mention Cog] 成就解鎖訊息已發送：{congratulatory_message}")
                                            print(f"[mention Cog] '{achievement_name}' 成就首次解鎖，開始生成圖片...")
                                            try:
                                                # 呼叫 image_generator.py 中的函式
                                                image_stream = await image_generator.generate_image_with_ai(
                                                    conversation_history = (response.text + add_text), # 傳遞完整的對話上下文
                                                    mode=user_current_mode,
                                                    image_name=f"first_unlock_{user_id}_{achievement_name}"  # 提供一個檔案名建議
                                                )
                                                if image_stream:
                                                    file = discord.File(image_stream, filename="generated_achievement_image.png") # Discord顯示的檔案名
                                                    
                                                    # 創建 Embed 來包裝圖片和文字
                                                    image_embed = discord.Embed(
                                                        title=f"🖼️ 首次成就紀念：{achievement_name}！",
                                                        description="要好好愛護貓貓喔!",
                                                        color=discord.Color.green() # 綠色代表成功/解鎖
                                                    )
                                                    image_embed.set_image(url="attachment://generated_achievement_image.png") # 指向附帶的圖片
                                                    image_embed.set_footer(text=f"獻給 {message.author.display_name} | 時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

                                                    # 發送訊息，包含文字內容、檔案和 Embed
                                                    await message.channel.send(
                                                        content=f"恭喜 <@{user_id}> 首次解鎖 **{achievement_name}**！",
                                                        file=file,
                                                        embed=image_embed,
                                                        reference=message
                                                    )
                                                    print(f"[mention Cog] 成功為 {user_id} 發送了首次解鎖 '{achievement_name}' 成就的圖片。")
                                                else:
                                                    await message.channel.send(f"抱歉，無法為首次解鎖的 '{achievement_name}' 成就生成圖片。", reference=message)
                                                    print(f"[mention Cog] 未能為 {user_id} 首次解鎖 '{achievement_name}' 成就生成圖片。")

                                            except Exception as img_e:
                                                print(f"[mention Cog] 生成或發送圖片時發生錯誤: {img_e}")
                                                await message.channel.send(f"生成圖片時發生錯誤：`{img_e}`", reference=message)

                                        break # 找到一個觸發短語就跳出，檢查下一個成就
                                    
                            await save_user_achievements_local(self.bot.user_achievements, USER_ACHIEVEMENTS_FILE)
                                #from main import save_user_achievements, USER_ACHIEVEMENTS_FILE
                                #await save_user_achievements(self.bot.user_achievements, USER_ACHIEVEMENTS_FILE)
                    except Exception as e:
                        print(f"[mention Cog] 處理成就時發生錯誤：{e}")
                            
                        # --- 成就檢查邏輯結束 ---
                        
                else:
                    await message.channel.send("Gemini 沒有生成有效的回答。", reference=message)
                        
            except Exception as e:
                print(f"[GeminiAI Cog] Error communicating with Gemini API: {e}")
                
        await self.bot.process_commands(message)

# Cog 檔案必須有一個 setup 函式，用來將 Cog 加入到機器人中
async def setup(bot):
    await bot.add_cog(MentionResponses(bot))