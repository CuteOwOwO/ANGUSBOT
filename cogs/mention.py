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
        self.TRIGGER_KEYWORDS = ["選卡包", "打手槍", "自慰", "漂亮寶寶", "忍不住了", "守羌", "射", "射一射"]

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

        # 【新加】先檢查訊息是否為指令，如果是指令，直接返回
        # 這可以避免重複處理指令，並確保 on_message 只處理非指令的 mention 訊息
        ctx = await self.bot.get_context(message)
        if ctx.command:
            return

        cleaned_content = message.clean_content.strip()

        # 檢查訊息是否包含機器人的標註
        # 並且不包含觸發卡包選擇的關鍵詞
        if self.bot.user in message.mentions and not any(keyword in cleaned_content for keyword in self.TRIGGER_KEYWORDS):
            # 【修改點 1】移除 async with message.typing():
            # 這裡直接執行後續邏輯，不再顯示機器人正在打字

            # 【新加】確保 user_id 存在於 self.bot.user_status
            user_id = message.author.id
            if user_id not in self.bot.user_status:
                self.bot.user_status[user_id] = {"state": "idle"}


            try:
                # 簡單的長度檢查，避免發送過長的問題給 API
                if len(cleaned_content) > 200:
                    await message.channel.send("問題太長了，請簡短一些。")
                    return

                # 檢查 self.model 是否已初始化
                if not self.model: #
                    await message.channel.send("Gemini AI 服務未啟用，請檢查 API 金鑰。")
                    return

                # 使用 generate_content 呼叫 Gemini API
                response = await self.model.generate_content(cleaned_content) #

                # 檢查是否有內容並傳送回 Discord
                if response and response.text:
                    # 【重要修正】移除重複發送的邏輯。
                    # 'last_message_id' 主要用於防止由於事件重複觸發導致的重複回覆
                    # 在 on_message 處理指令和普通消息的正確分離後，
                    # 這裡的 'last_message_id' 判斷在 on_message 中通常不再需要，
                    # 因為每個消息只會被處理一次（要么是指令，要么是非指令消息）。
                    # 如果仍然有重複，那可能是 bot.run() 被重複執行了。

                    # 這裡先獲取，如果不存在就初始化它
                    # 確保 self.bot.user_status[user_id] 存在
                    if user_id not in self.bot.user_status:
                        self.bot.user_status[user_id] = {}

                    # 因為 GeminiAI Cog 的 on_message 應該只處理非指令的 mention 訊息，
                    # 所以這裡的 last_message_id 判斷主要是為了防止同一條訊息被意外處理多次。
                    # 這是你原始程式碼就有的邏輯，可以保留，但其作用更多是防護性的。
                    user_last_message_id = self.bot.user_status[user_id].get("last_message_id")
                    if user_last_message_id == message.id:
                        print(f"[GeminiAI Cog] 偵測到重複訊息 ID {message.id}，已忽略。")
                        return

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