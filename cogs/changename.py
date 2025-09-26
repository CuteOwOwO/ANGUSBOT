import discord
from discord.ext import commands
from datetime import datetime
import asyncio

class NicknameChanger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 設定要監聽的頻道 ID (請替換為實際的頻道 ID)

        self.target_channel_id = 884006952731017272  # <-- 請替換為你要監聽的頻道 ID
        # 設定目標伺服器 ID (請替換為實際的伺服器 ID) 
        self.target_guild_id = 884006952731017267    # <-- 請替換為你的伺服器 ID
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """
        監聽訊息事件，當用戶在指定頻道發言時修改其暱稱
        """
        # 忽略 bot 自己的訊息
        if message.author.bot:
            return
            
        # 檢查是否為指定的頻道
        if message.channel.id != self.target_channel_id:
            return
            
        # 獲取目標伺服器
        guild = self.bot.get_guild(self.target_guild_id)
        if not guild:
            print(f"找不到 ID 為 {self.target_guild_id} 的伺服器")
            return
        print(f"偵測到來自 {message.author.name} 的訊息，準備修改暱稱...")
        # 獲取該用戶在目標伺服器中的成員物件
        member = guild.get_member(message.author.id)
        if not member:
            print(f"用戶 {message.author.name} 不在目標伺服器中")
            return
            
        # 獲取訊息內容作為新暱稱
        new_nickname = message.content.strip()
        
        # 檢查暱稱長度限制 (Discord 限制為 32 個字符)
        if len(new_nickname) > 32:
            new_nickname = new_nickname[:32]
            
        # 如果訊息為空或只有空白，則不進行修改
        if not new_nickname:
            return
            
        try:
            # 修改用戶在伺服器中的暱稱
            await member.edit(nick=new_nickname)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已將用戶 {message.author.name} 的暱稱修改為: {new_nickname}")
            
            # 可選：在頻道中回覆確認訊息 (如果不需要可以註解掉)
            await message.reply(f"已將你的暱稱修改為: {new_nickname}", delete_after=5)
            
        except discord.Forbidden:
            print(f"權限不足，無法修改用戶 {message.author.name} 的暱稱")
            # 可選：通知用戶權限不足 (如果不需要可以註解掉)
            await message.reply("抱歉，我沒有權限修改你的暱稱", delete_after=5)
            
        except discord.HTTPException as e:
            print(f"修改用戶 {message.author.name} 暱稱時發生錯誤: {e}")
            
        except Exception as e:
            print(f"未預期的錯誤: {e}")

    @commands.command(name="setnick")
    @commands.has_permissions(manage_nicknames=True)
    async def manual_set_nickname(self, ctx, member: discord.Member, *, nickname):
        """
        手動設定用戶暱稱的指令 (需要管理暱稱權限)
        用法: !setnick @用戶 新暱稱
        """
        try:
            # 檢查暱稱長度限制
            if len(nickname) > 32:
                nickname = nickname[:32]
                
            await member.edit(nick=nickname)
            await ctx.send(f"已將 {member.mention} 的暱稱修改為: {nickname}")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {ctx.author.name} 手動將 {member.name} 的暱稱修改為: {nickname}")
            
        except discord.Forbidden:
            await ctx.send("我沒有權限修改該用戶的暱稱")
            
        except discord.HTTPException as e:
            await ctx.send(f"修改暱稱時發生錯誤: {e}")

    @commands.command(name="clearnick")
    @commands.has_permissions(manage_nicknames=True)
    async def clear_nickname(self, ctx, member: discord.Member):
        """
        清除用戶暱稱的指令 (恢復為原始用戶名)
        用法: !clearnick @用戶
        """
        try:
            await member.edit(nick=None)
            await ctx.send(f"已清除 {member.mention} 的暱稱")
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {ctx.author.name} 清除了 {member.name} 的暱稱")
            
        except discord.Forbidden:
            await ctx.send("我沒有權限修改該用戶的暱稱")
            
        except discord.HTTPException as e:
            await ctx.send(f"清除暱稱時發生錯誤: {e}")

# Cog 檔案必須有一個 setup 函式
async def setup(bot):

    await bot.add_cog(NicknameChanger(bot))



