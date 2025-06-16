# cogs/gemini_ai.py

import os
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# 從環境變數中獲取 Gemini API 金鑰
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class GeminiAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = None # 初始化為 None
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)

                self.model = genai.GenerativeModel('gemini-2.5-flash-latest')
                print("[GeminiAI Cog] Gemini API configured successfully using gemini-2.5-flash-latest!")
            except Exception as e:
                print(f"[GeminiAI Cog] Error configuring Gemini API: {e}")
                print("請檢查您的 GEMINI_API_KEY 是否正確。")
        else:
            print("[GeminiAI Cog] GEMINI_API_KEY not found in .env file. Gemini features will be disabled.")

    @commands.command(name='gemini', help='向 Gemini 提問。例如: %gemini 什麼是生成式AI?')
    async def ask_gemini(self, ctx, *, question: str):
        """
        處理基於前綴的 Gemini 提問指令。
        """
        if not self.model:
            await ctx.send("Gemini 功能尚未啟用，因為缺少 API 金鑰或配置錯誤。")
            return

        # 顯示 Bot 正在「打字中」的狀態
        async with ctx.typing():
            try:
                # 簡單的長度檢查，避免發送過長的問題給 API
                if len(question) > 200: # 粗略估計，實際應考慮 token 數量
                    await ctx.send("問題太長了，請簡短一些。")
                    return

                # 使用 generate_content 呼叫 Gemini API
                response = self.model.generate_content(question)
                
                # 檢查是否有內容並傳送回 Discord
                if response and response.text:
                    # Discord 訊息長度限制為 2000 字元
                    if len(response.text) > 2000:
                        await ctx.send("答案太長了，將分段發送：")
                        # 將答案分割成多條訊息，每條不超過 1990 字元 (留一些空間給 ``` 和標點)
                        chunks = [response.text[i:i+1990] for i in range(0, len(response.text), 1990)]
                        for chunk in chunks:
                            await ctx.send(f"```{chunk}```") # 使用 Markdown 程式碼區塊格式化
                    else:
                        await ctx.send(f"```{response.text}```") # 使用 Markdown 程式碼區塊格式化
                else:
                    await ctx.send("Gemini 沒有生成有效的回答。")

            except Exception as e:
                print(f"[GeminiAI Cog] Error communicating with Gemini API: {e}")
                # 捕獲並回應錯誤訊息
                await ctx.send(f"在與 Gemini 溝通時發生錯誤：`{e}`")
                await ctx.send("請檢查您的問題或稍後再試。")

    # 你也可以選擇添加斜線指令版本，讓用戶有更多選擇
    # 注意：斜線指令需要 Bot 具有 applications.commands 權限
    @commands.slash_command(name="gemini", description="向 Gemini AI 提問")
    async def gemini_slash(self, ctx: discord.ApplicationContext, question: str):
        """
        處理斜線指令版本的 Gemini 提問。
        """
        if not self.model:
            await ctx.respond("Gemini 功能尚未啟用，因為缺少 API 金鑰或配置錯誤。", ephemeral=True)
            return

        await ctx.defer() # 延遲回應，因為 API 可能需要一些時間

        try:
            if len(question) > 2000:
                await ctx.followup.send("問題太長了，請簡短一些。", ephemeral=True)
                return

            response = self.model.generate_content(question)

            if response and response.text:
                if len(response.text) > 2000:
                    await ctx.followup.send("答案太長了，將分段發送：")
                    chunks = [response.text[i:i+1990] for i in range(0, len(response.text), 1990)]
                    for chunk in chunks:
                        await ctx.followup.send(f"```{chunk}```")
                else:
                    await ctx.followup.send(f"```{response.text}```")
            else:
                await ctx.followup.send("Gemini 沒有生成有效的回答。")

        except Exception as e:
            print(f"[GeminiAI Cog] Error communicating with Gemini API: {e}")
            await ctx.followup.send(f"在與 Gemini 溝通時發生錯誤：`{e}` 請檢查您的問題或稍後再試。")


# setup 函數是 discord.py 加載 cog 的入口點
async def setup(bot):
    await bot.add_cog(GeminiAI(bot))