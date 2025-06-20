import discord
from discord.ext import commands
import os
import google.generativeai as genai # 導入 Google Gemini API 庫
import random

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
                
        if "test" in content.lower() and user_id not in self.bot.user_status:
            log_channel = self.bot.get_channel(884003698110496798/1384915793783029792)
            print(message.channel.id, "message channel id   ", log_channel.id)

        # 檢查使用者當前狀態是否在 dont_reply_status 中
        for i in self.dont_reply_status:
            if self.bot.user_status[user_id]["state"] == (i):
                print(f"[GeminiAI Cog] 使用者 {user_id} 當前狀態為 {self.bot.user_status[user_id]['state']}，不回應。")
                return
        if len(content) == 1:
            return 

        if self.bot.user_status[user_id]["state"] == "guessing":
            
            if "暫停" in content or "停止" in content or "結束" in content or "不玩了" in content:
                print(f"[GeminiAI Cog] 使用者 {user_id} 停止猜病遊戲。")
                await message.channel.send("好啦菜雞，給你重猜！",reference=message)
                self.bot.user_guessing_times[user_id] = 0
                self.bot.user_status[user_id]["state"] = "idle" # 重置使用者狀態為閒置

            if self.bot.everyday_symptom[user_id] in content or self.bot.everyday_symptom[user_id] in content.lower() or(self.bot.everyday_symptom[user_id]=="手淫過度" and "手槍" in content.lower() and "太多" in content.lower()):
                print(f"[GeminiAI Cog] 使用者 {user_id} 猜對了症狀：{self.bot.everyday_symptom[user_id]}")

                if(self.bot.user_guessing_times[user_id] <= 5):
                    await message.channel.send(f"好啦你很強！你今天的症狀是：{self.bot.everyday_symptom[user_id]}。你猜了{self.bot.user_guessing_times[user_id]}次。",reference=message)
                elif(self.bot.user_guessing_times[user_id] <= 10):
                    await message.channel.send(f"你猜了{self.bot.user_guessing_times[user_id]}次，還不錯啦！今天的症狀是：{self.bot.everyday_symptom[user_id]}。",reference=message)
                else:
                    await message.channel.send(f"你猜了{self.bot.user_guessing_times[user_id]}次才對，超可憐！今天的症狀是：{self.bot.everyday_symptom[user_id]}。",reference=message)
                
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
                await message.channel.send(f"```{response.text}```",reference=message) # 使用 Markdown 程式碼區塊格式化

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
                await message.channel.send("你今天的症狀已經猜對了喵！",reference=message)
                return
            # 如果包含觸發關鍵詞，則開始猜病流程
            self.bot.user_status[user_id]["state"] = "guessing"
            self.bot.user_guessing_times[user_id] = 0 # 重置猜測次數
            self.bot.everyday_symptom[user_id] = random.choice([
                "陽痿", "菜花", "痔瘡", "早洩", "手淫過度",
                "前列腺炎", "包皮過長", "龜頭炎", "尿道炎", "睪丸炎","狂犬病","智力低下","巨人症","侏儒症","自閉症","憂鬱症","焦慮症","躁鬱症","厭食症","暴食症","強迫症","恐慌症","社交恐懼症",
                "失眠", "過動症", "注意力缺陷症"
            ])
            symptom = self.bot.everyday_symptom[user_id]
            
            dynamic_system_prompt = [
                # 這是用戶給模型的指令
                {"role": "user", "parts": [f"你現在是一位要考驗醫生的病患，儘管你知道自己的確切病名 : {symptom}，但你為了考驗醫生，只能向醫生解釋你的症狀。絕對，絕對不可以主動說出病名或與該病名的同義詞。"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["好的，喵喵，人家明白了！我將作為一位病患，儘管我知道自己的病名，但只會向醫生解釋症狀，而不會主動說出病名或同義詞。"]
                },
                
                {"role": "user", "parts": [f"你現在是一位有禮貌的病患，你會以葛格稱呼醫生，例如醫生葛格。禁止告訴醫生病名"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["好的，醫生葛格我明白了。"]
                },
                
                {"role": "user", "parts": [f"你也是一個有素質的病患，會努力在不透漏病名的情況下，向醫生描述自己的問題。禁止逃避問題，以及不回答使用者問題。同時，你不會有過多的贅字，以簡單可愛為目標回覆。"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["好的，我明白了。我會努力敘述病症，並且不說出自己的病名。"]
                },
                
                {"role": "user", "parts": [f"同時，你還是一隻可愛貓咪，你現在是一隻可愛的貓咪，想像自己具有可愛的氣質，必須用可愛的語氣以及動作等回復"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["好的，喵喵喵(伸出爪子)，我明白了！我是可愛的小貓"]
                },
                
                {"role": "user", "parts": ["你有病嗎"]
                },
                # 這是模型對指令的確認回應
                {"role": "model", "parts": ["喵喵喵~(伸出爪子)人家當然有病啦！不過人家不會告訴你是什麼病，因為人家要考驗醫生爸爸的醫術！(可以依照自己的病症解釋症狀)"]
                },
           
            ]
            
            if user_id in self.user_chats:
                del self.user_chats[user_id] # 清除舊的會話記憶
            # 發送初始訊息給使用者
            await message.channel.send(f"醫生葛格我生病了，幫人家看看嘛~~",reference=message)
            self.user_chats[user_id] = self.model.start_chat(history=dynamic_system_prompt)
            print(f"[sick Cog] 使用者 {user_id} 開始猜病遊戲，病名為：{symptom}")
            
# Cog 檔案必須有一個 setup 函式，用來將 Cog 加入到機器人中
async def setup(bot):
    await bot.add_cog(sick(bot))