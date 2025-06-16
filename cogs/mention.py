import discord
from discord.ext import commands
import os

class MentionResponses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TRIGGER_KEYWORDS = ["選卡包", "打手槍", "自慰", "漂亮寶寶", "忍不住了", "守羌", "射", "射一射"]
    # 監聽 on_message 事件
    @commands.Cog.listener()
    async def on_message(self, message):
        # 排除機器人本身的訊息，避免無限循環
        if message.author == self.bot.user:
            return

        # 檢查訊息是否包含機器人的標註
        # message.mentions 是一個列表，包含了所有被標註的使用者物件
        # self.bot.user 是機器人自己的使用者物件
        cleaned_content = message.clean_content.strip()
        if self.bot.user in message.mentions and not any(keyword in cleaned_content for keyword in self.TRIGGER_KEYWORDS):
            
            async with message.typing():
                try:
                    # 簡單的長度檢查，避免發送過長的問題給 API
                    if len(cleaned_content) > 200: # 粗略估計，實際應考慮 token 數量
                        await message.channel.send("問題太長了，請簡短一些。")
                        return

                # 使用 generate_content 呼叫 Gemini API
                    response = self.model.generate_content(cleaned_content)

                    # 檢查是否有內容並傳送回 Discord
                    if response and response.text:
                        if self.bot.user_status.get("last_message_id") == message.id:
                            return
                        # Discord 訊息長度限制為 2000 字元
                        if len(response.text) > 2000:
                            await message.channel.send("答案太長了，將分段發送：")
                            # 將答案分割成多條訊息，每條不超過 1990 字元 (留一些空間給 ``` 和標點)
                            chunks = [response.text[i:i+1990] for i in range(0, len(response.text), 1990)]
                            if self.bot.user_status.get("last_message_id"):
                                return
                            for chunk in chunks:
                                await message.channel.send(f"```{chunk}```") # 使用 Markdown 程式碼區塊格式化
                            self.bot.user_status["last_message_id"] = message.id
                        else:
                            if self.bot.user_status.get("last_message_id"):
                                return
                            await message.channel.send(f"```{response.text}```") # 使用 Markdown 程式碼區塊格式化
                            self.bot.user_status["last_message_id"] = message.id
                        print(f"[GeminiAI Cog] 回答成功發送：{response.text[:50]}...") # 日誌前50個字元
                        print(message.id, "message id" , self.bot.user_status["last_message_id"])
                    else:
                        await message.channel.send("Gemini 沒有生成有效的回答。")
                    self.bot.user_status["last_message_id"] = message.id
                except Exception as e:
                    print(f"[GeminiAI Cog] Error communicating with Gemini API: {e}")
                    # 捕獲並回應錯誤訊息
                    await message.channel.send(f"在與 Gemini 溝通時發生錯誤：`{e}`")
                    await message.channel.send("請檢查您的問題或稍後再試。")

            # 處理完自定義的 on_message 邏輯後，
            # 必須呼叫 bot.process_commands 讓指令系統也能處理這條訊息
            # 這樣，如果使用者標註機器人後又輸入了指令，機器人依然能回應指令
            await self.bot.process_commands(message)


# Cog 檔案必須有一個 setup 函式，用來將 Cog 加入到機器人中
async def setup(bot):
    await bot.add_cog(MentionResponses(bot))