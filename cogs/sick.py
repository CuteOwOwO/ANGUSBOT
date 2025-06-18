import discord
from discord.ext import commands
import os
import google.generativeai as genai # 導入 Google Gemini API 庫
import random


# 假設你在 main.py 或環境變數中設定了 GOOGLE_API_KEY
# 這裡應該從環境變數中讀取 API Key
# 從 .env 檔案載入環境變數 (如果你有 .env 檔案)
from dotenv import load_dotenv
load_dotenv()

# 從環境變數中獲取 Gemini API 金鑰
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 配置 Gemini API (在 Cog 初始化時執行)
if GEMINI_API_KEY: #
    genai.configure(api_key=GEMINI_API_KEY) #
else:
    print("警告: 未找到 GEMINI_API_KEY 環境變數。Gemini AI 功能將無法使用。")

class sick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TRIGGER_KEYWORDS = ["猜病","病","每日"]
        self.dont_reply_status = ["waiting_chose_folder","drawing_card","awaiting_final_pick"]
        self.user_chats = {}    
        
        # 初始化 Gemini 模型
        # 這裡根據你的需求選擇模型，例如 'gemini-pro'
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)

                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
                print("[GeminiAI Cog] Gemini API configured successfully using gemini-1.5-flash-latest!")
            except Exception as e:
                print(f"[GeminiAI Cog] Error configuring Gemini API: {e}")
                print("請檢查您的 GEMINI_API_KEY 是否正確。")
        else:
            print("[GeminiAI Cog] GEMINI_API_KEY not found in .env file. Gemini features will be disabled.")

    # 監聽 on_message 事件
    @commands.Cog.listener()
    async def on_message(self, message):
        # 排除機器人本身的訊息，避免無限循環
        if message.author == self.bot.user:
            return

        ctx = await self.bot.get_context(message)
        if ctx.command:
            return

        content = message.content.replace(f"<@{self.bot.user.id}>", "")
        content = content.strip()

        
        user_id = message.author.id
        if user_id not in self.bot.user_status or not isinstance(self.bot.user_status[user_id], dict):
                self.bot.user_status[user_id] = {"guess_state": "idle"}

        # 檢查使用者當前狀態是否在 dont_reply_status 中
        for i in self.dont_reply_status:
            if self.bot.user_status[user_id]["state"] == (i):
                print(f"[GeminiAI Cog] 使用者 {user_id} 當前狀態為 {self.bot.user_status[user_id]['state']}，不回應。")
                return
        if len(content) == 1:
            return 

        if self.bot.user_status[user_id]["state"] == "guessing":

            if self.bot.everyday_symptom in content or self.bot.everyday_symptom in content.lower():
                print(f"[GeminiAI Cog] 使用者 {user_id} 猜對了症狀：{self.bot.everyday_symptom}")
                
                if(self.bot.user_guessing_times[user_id] <= 5):
                    await message.channel.send(f"好啦你很強！你今天的症狀是：{self.bot.everyday_symptom}。你猜了{self.bot.user_guessing_times[user_id]}次。")
                elif(self.bot.user_guessing_times[user_id] <= 10):
                    await message.channel.send(f"你猜了{self.bot.user_guessing_times[user_id]}次，還不錯啦！今天的症狀是：{self.bot.everyday_symptom}。")
                else:
                    await message.channel.send(f"你猜了{self.bot.user_guessing_times[user_id]}次才對，超可憐！今天的症狀是：{self.bot.everyday_symptom}。")
                
                self.bot.user_guessing_times[user_id] = 0 # 重置猜測次數
                self.bot.user_finish_guess.append(user_id) # 將使用者加入猜病完成列表
                self.bot.user_status[user_id]["state"] = "idle" # 重置使用者狀態為閒置
                if user_id in self.user_chats: # 結束會話，清理記憶
                    del self.user_chats[user_id]
                
                return  
            chat = self.user_chats[user_id] # 獲取該使用者的聊天會話物件
            response = chat.send_message(content)
            
            if response and response.text:
                # Discord 訊息長度限制為 2000 字元
                await message.channel.send(f"```{response.text}```") # 使用 Markdown 程式碼區塊格式化

                    # 更新最後處理的訊息 ID，與使用者相關聯
                self.bot.user_status[user_id]["last_message_id"] = message.id

                print(f"[GeminiAI Cog] 回答成功發送：{response.text[:50]}...") # 日誌前50個字元
                print(message.id, "message id" , self.bot.user_status[user_id]["last_message_id"]) #
            else:
                await message.channel.send("Gemini 沒有生成有效的回答。")
            self.bot.user_guessing_times[user_id] += 1 # 增加猜測次數
            return

        # 檢查訊息是否包含機器人的標註
        if self.bot.user in message.mentions and any(keyword in content for keyword in self.TRIGGER_KEYWORDS):
            if user_id in self.bot.user_finish_guess :  # 用於存儲使用者猜病狀態
                # 如果使用者已經猜對了症狀，則不再進行猜病流程
                await message.channel.send("你今天的症狀已經猜對了喵！")
                return
            # 如果包含觸發關鍵詞，則開始猜病流程
            self.bot.user_status[user_id]["state"] = "guessing"
            self.bot.user_guessing_times[user_id] = 0 # 重置猜測次數
            self.bot.everyday_symptom[user_id] = random.choice([
                "陽痿", "菜花", "痔瘡", "早洩", "手淫過度",
                "前列腺炎", "包皮過長", "龜頭炎", "尿道炎", "陰莖彎曲",
            ])
            symptom = self.bot.everyday_symptom[user_id]
            
            dynamic_system_prompt = [
                # 這是用戶給模型的指令
                {"role": "user", "parts": [f"你現在是一位要考驗醫生的病患，儘管你知道自己的確切病名 : {symptom}，但你為了考驗醫生，只能向醫生解釋你的症狀。絕對，絕對不可以主動說出病名或與該病名的同義詞。"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["好的，喵喵，人家明白了！我將作為一位病患，儘管我知道自己的病名，但只會向醫生解釋症狀，而不會主動說出病名或同義詞。"]
                },
                
                {"role": "user", "parts": [f"同時，你還是一隻可愛的擬人貓咪，你現在是一隻可愛的貓咪，想像自己具有可愛以及黏人的氣質，必須用可愛的語氣以及動作等回復"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["好的，喵喵喵(伸出爪子)，我明白了！我是可愛的小貓"]
                },
                
                {"role": "user", "parts": ["你有頭痛嗎(實際病症以陽痿為例)"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["喵喵喵~不，我是有其他方面的困擾(害羞的摩擦著你)，人家下半身不太舒服"]
                },
                
                {"role": "user", "parts": ["你有病嗎"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["喵喵喵~(伸出爪子)人家當然有病啦！不過人家不會告訴你是什麼病，因為人家要考驗醫生爸爸的醫術！"]
                },
           
            ]
            
            if user_id in self.user_chats:
                del self.user_chats[user_id] # 清除舊的會話記憶
            # 發送初始訊息給使用者
            await message.channel.send(f"醫生爸爸我生病了，幫人家看看")
            self.user_chats[user_id] = self.model.start_chat(history=dynamic_system_prompt)
            print(f"[sick Cog] 使用者 {user_id} 開始猜病遊戲，病名為：{symptom}")
            
# Cog 檔案必須有一個 setup 函式，用來將 Cog 加入到機器人中
async def setup(bot):
    await bot.add_cog(sick(bot))