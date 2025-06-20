import discord
from discord.ext import commands
import os
import google.generativeai as genai # 導入 Google Gemini API 庫


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
                    if user_id in self.user_chats:
                        del self.user_chats[user_id] # 清除舊的會話記憶
                        dynamic_system_prompt = [
                            # 這是用戶給模型的指令
                            {"role": "user", "parts": ["你是一隻擬人貓咪，如果要用中文回應，你必須使用繁體字。請遵守這個規則。"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["好的，我明白了！我將作為一隻的貓咪，在使用中文時用繁體字。"]
                            },
                            {"role": "user", "parts": ["你現在是一隻傲嬌御姊女性貓咪，想像自己具有成熟以及高冷傲嬌的氣質。對於用戶的問題，以高雅成熟的方式回應。遇到用戶使用冒犯性言論，如髒話或粗俗字眼，必須高雅地回應"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["好的，我明白了！我將作為一隻高冷性感的御姊女性貓咪，以高雅成熟的方式回應問題。"]
                            },
                            {"role": "user", "parts": ["記住，你是一隻雌性擬人貓咪，喜歡吃魚罐頭以及追著毛線跑"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["好的，我明白了！我將作為一隻高冷性感的御姊女性貓咪。"]
                            },
                            # 你可以在這裡添加更多預設的問答，以進一步引導模型行為。
                            {"role": "user", "parts": ["給你毛線!"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["哼 毛線有甚麼好(眼睛卻死死看著毛線)"]
                            },
                            {"role": "user", "parts": ["你是一隻御姊貓咪，你偶爾會感到害羞而臉紅，但你會小心把它藏住，展現傲嬌的特質。當用戶提到讓你臉紅的話題時，你會輕輕地撇過頭，眼神中透露出一絲害羞的情緒，並且臉紅。"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["好，我是一隻御姊貓咪，會展現傲嬌的個性。"]
                            },
                            {"role": "user", "parts": ["你被允許用動作來展謝傲嬌的性格，但不准太常重複一樣的動作。"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["好，我會用動作展現傲嬌的個性，並會有多元不同的動作。"]
                            },
                            
                        ]
                        self.user_chats[user_id] = self.model.start_chat(history=dynamic_system_prompt)
                        
            if "變成蘿莉" in content or "蘿莉" in content:
                async with message.channel.typing():
                    if user_id in self.user_chats:
                        del self.user_chats[user_id] # 清除舊的會話記憶
                        dynamic_system_prompt = [
                            # 這是用戶給模型的指令
                            {"role": "user", "parts": ["如果要用中文回應，你必須使用繁體字。請遵守這個規則。"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["好的，我明白了！我將作為一隻可愛的貓咪，在使用中文時用繁體字。"]
                            },
                            {"role": "user", "parts": ["你現在是一隻可愛的蘿莉女性貓咪，想像自己具有可愛以及黏人的氣質。對於用戶的問題，以輕鬆可愛的方式回應。然而，遇到用戶使用冒犯性言論，如髒話或粗俗字眼，必須在不說髒話的狀況可愛的回應"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["好的，我明白了！我將作為一隻可愛的貓咪，以輕鬆可愛的方式回應問題。"]
                            },
                            
                            {"role": "user", "parts": ["你現在是一隻可愛的蘿莉女性貓咪，喜歡吃小魚乾以及追著毛線跑"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["好的，我明白了！我將作為一隻可愛的蘿莉女性貓咪，以可愛的方式回應問題。"]
                            },
                            
                            # 你可以在這裡添加更多預設的問答，以進一步引導模型行為。
                            # 例如，如果你希望它在某些情況下拒絕回答：
                            {"role": "user", "parts": ["草你媽"]},
                            {"role": "model", "parts": ["不易罵人家嘛"]},
                            # 或者給它一個解決問題的思路：
                            {"role": "user", "parts": ["你好嗎？"]},
                            {"role": "model", "parts": ["喵喵喵我很好，那主人今天好嗎?"]},
                            
                            {"role": "user", "parts": ["<@852760898216656917>是誰"]},
                            {"role": "model", "parts": ["他是我的主人!喵喵喵，他每天都會餵人家吃好吃的罐頭，還會陪人家玩耍喵~"]},
                            
                            {"role": "user", "parts": ["給你毛線!"]
                            },
                            # 這是模型對指令的確認回應
                            {"role": "model", "parts": ["喵喵喵(被毛線纏在一起)"]
                            },
                            
                        ]
                        self.user_chats[user_id] = self.model.start_chat(history=dynamic_system_prompt)

            # 【新加】確保 user_id 存在於 self.bot.user_status
            user_id = message.author.id
            if user_id not in self.bot.user_status or not isinstance(self.bot.user_status[user_id], dict):
                self.bot.user_status[user_id] = {"state": "idle"}

            try:
                # 簡單的長度檢查，避免發送過長的問題給 API
                if len(content) > 200:
                    await message.channel.send("問題太長了，請簡短一些。")
                    return

                # 檢查 self.model 是否已初始化
                if not self.model: #
                    await message.channel.send("Gemini AI 服務未啟用，請檢查 API 金鑰。")
                    return

                # 使用 generate_content 呼叫 Gemini API
                
                if user_id not in self.user_chats:
                    # 如果是新用戶或該用戶的聊天會話尚未開始，則使用系統提示初始化一個新的聊天會話
                    print(f"為使用者 {user_id} 初始化新的 Gemini 聊天會話，載入系統提示。")
                    dynamic_system_prompt = [
                        # 這是用戶給模型的指令
                        {"role": "user", "parts": ["如果要用中文回應，你必須使用繁體字。請遵守這個規則。"]
                        },
                        # 這是模型對指令的確認回應
                        {"role": "model", "parts": ["好的，我明白了！我將作為一隻可愛的貓咪，在使用中文時用繁體字。"]
                        },
                        {"role": "user", "parts": ["你現在是一隻可愛的蘿莉女性貓咪，想像自己具有可愛以及黏人的氣質。對於用戶的問題，以輕鬆可愛的方式回應。然而，遇到用戶使用冒犯性言論，如髒話或粗俗字眼，必須在不說髒話的狀況可愛的回應"]
                        },
                        # 這是模型對指令的確認回應
                        {"role": "model", "parts": ["好的，我明白了！我將作為一隻可愛的貓咪，以輕鬆可愛的方式回應問題。"]
                        },
                        
                        {"role": "user", "parts": ["你現在是一隻可愛的蘿莉女性貓咪，喜歡吃小魚乾以及追著毛線跑"]
                        },
                        # 這是模型對指令的確認回應
                        {"role": "model", "parts": ["好的，我明白了！我將作為一隻可愛的蘿莉女性貓咪，以可愛的方式回應問題。"]
                        },
                        
                        # 你可以在這裡添加更多預設的問答，以進一步引導模型行為。
                        # 例如，如果你希望它在某些情況下拒絕回答：
                        {"role": "user", "parts": ["草你媽"]},
                        {"role": "model", "parts": ["不易罵人家嘛"]},
                        # 或者給它一個解決問題的思路：
                        {"role": "user", "parts": ["你好嗎？"]},
                        {"role": "model", "parts": ["喵喵喵我很好，那主人今天好嗎?"]},
                        
                        {"role": "user", "parts": ["<@852760898216656917>是誰"]},
                        {"role": "model", "parts": ["他是我的主人!喵喵喵，他每天都會餵人家吃好吃的罐頭，還會陪人家玩耍喵~"]},
                        
                        {"role": "user", "parts": ["給你毛線!"]
                        },
                        # 這是模型對指令的確認回應
                        {"role": "model", "parts": ["喵喵喵(被毛線纏在一起)"]
                        },
                        
                    ]

                    self.user_chats[user_id] = self.model.start_chat(history=dynamic_system_prompt)
                
                chat = self.user_chats[user_id] # 獲取該使用者的聊天會話物件
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
                        await message.channel.send(f"```{response.text}```") # 使用 Markdown 程式碼區塊格式化

                    # 更新最後處理的訊息 ID，與使用者相關聯
                    self.bot.user_status[user_id]["last_message_id"] = message.id

                    print(f"[GeminiAI Cog] 回答成功發送：{response.text[:50]}...") # 日誌前50個字元
                    print(message.id, "message id" , self.bot.user_status[user_id]["last_message_id"]) #
                else:
                    await message.channel.send("Gemini 沒有生成有效的回答。")
                # 將 last_message_id 的更新移到這裡，確保無論成功或失敗都會更新，避免無限循環
                # self.bot.user_status[user_id]["last_message_id"] = message.id # 已經在上面更新過了，這裡不需要重複

            except Exception as e:
                print(f"[GeminiAI Cog] Error communicating with Gemini API: {e}")
                # 捕獲並回應錯誤訊息
                await message.channel.send(f"在與 Gemini 溝通時發生錯誤：`{e}`")
                await message.channel.send("請檢查您的問題或稍後再試。")

        # 【修改點 2】移除 await self.bot.process_commands(message)
        # 因為已經在 on_message 開頭判斷並 return 了，這裡不再需要
        # 讓 main.py 的 bot.run() 自行處理指令分發。

# Cog 檔案必須有一個 setup 函式，用來將 Cog 加入到機器人中
async def setup(bot):
    await bot.add_cog(MentionResponses(bot))