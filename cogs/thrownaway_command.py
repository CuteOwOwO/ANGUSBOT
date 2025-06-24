import discord
from discord.ext import commands

# 每個 Cog 必須是一個繼承 commands.Cog 的類別
class General(commands.Cog):
    def __init__(self, bot):
        # 儲存 bot 實例，以便在 Cog 中使用 bot 的功能
        self.bot = bot

    # 定義你的指令，使用 @commands.command() 裝飾器
   
    @commands.command(name="Hello") # 指令名稱預設為函式名，但你可以明確指定
    async def hello_command(self, ctx):
        # 回覆 Hello, world!
        await ctx.send("Hello, world!")
        
    @commands.command(name="吃什麼" or "吃啥")
    async def eat_command(self, ctx):
        # 回覆隨機的食物建議
        await ctx.send("吃我屌")  # 這裡可以隨機選擇食物
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

# Cog 檔案必須有一個 setup 函式，用來將 Cog 加入到機器人中
# 機器人啟動時會自動呼叫這個函式
'''async def setup(bot):
    await bot.add_cog(General(bot))'''