import discord
from discord.ext import commands
import os

class MentionResponses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # 監聽 on_message 事件
    @commands.Cog.listener()
    async def on_message(self, message):
        # 排除機器人本身的訊息，避免無限循環
        if message.author == self.bot.user:
            return

        # 檢查訊息是否包含機器人的標註
        # message.mentions 是一個列表，包含了所有被標註的使用者物件
        # self.bot.user 是機器人自己的使用者物件
        
        if self.bot.user in message.mentions:
            cleaned_content = message.clean_content.strip()
            if "休息" in cleaned_content:
                await message.channel.send("主人請您好好休息")
            if cleaned_content == "吵屁吵":
                await message.channel.send("你才吵屁吵")
            elif cleaned_content == "吵屁":
                await message.channel.send("吵屁吵")

            # 處理完自定義的 on_message 邏輯後，
            # 必須呼叫 bot.process_commands 讓指令系統也能處理這條訊息
            # 這樣，如果使用者標註機器人後又輸入了指令，機器人依然能回應指令
            await self.bot.process_commands(message)


# Cog 檔案必須有一個 setup 函式，用來將 Cog 加入到機器人中
async def setup(bot):
    await bot.add_cog(MentionResponses(bot))