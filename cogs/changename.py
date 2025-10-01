import discord
from discord.ext import commands
from datetime import datetime
import asyncio

class NicknameChanger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # 設定頻道與伺服器的對應關係
        self.channel_guild_map = {
            1421064552459669646: 1421064550878412841,  # 原本的頻道 -> 原本的伺服器
            1405431029736542329: 1403353787229274164,  # 新頻道 -> 新伺服器
        }
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """
        監聽訊息事件,當用戶在指定頻道發言時修改其暱稱
        """
        # 忽略 bot 自己的訊息
        if message.author.bot:
            return
            
        # 檢查訊息頻道是否在監聽列表中
        if message.channel.id not in self.channel_guild_map:
            return
        
        # 根據頻道 ID 獲取對應的伺服器 ID
        target_guild_id = self.channel_guild_map[message.channel.id]
        
        # 獲取目標伺服器
        guild = self.bot.get_guild(target_guild_id)
        if not guild:
            print(f"找不到 ID 為 {target_guild_id} 的伺服器")
            return
            
        print(f"偵測到來自 {message.author.name} 的訊息 (頻道: {message.channel.id}),準備修改暱稱...")
        
        # 獲取該用戶在目標伺服器中的成員物件
        member = guild.get_member(message.author.id)
        if not member:
            print(f"用戶 {message.author.name} 不在目標伺服器 {guild.name} 中")
            return
            
        # 獲取訊息內容作為新暱稱
        new_nickname = message.content.strip()
        
        # 檢查暱稱長度限制 (Discord 限制為 32 個字符)
        if len(new_nickname) > 32:
            new_nickname = new_nickname[:32]
            
        # 如果訊息為空或只有空白,則不進行修改
        if not new_nickname:
            return
            
        try:
            # 修改用戶在伺服器中的暱稱
            await member.edit(nick=new_nickname)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 已將用戶 {message.author.name} 在伺服器 {guild.name} 的暱稱修改為: {new_nickname}")
            
            # 可選:在頻道中回覆確認訊息 (如果不需要可以註解掉)
            await message.reply(f"已將你的暱稱修改為: {new_nickname}", delete_after=5)
            
        except discord.Forbidden:
            print(f"權限不足,無法修改用戶 {message.author.name} 的暱稱")
            # 可選:通知用戶權限不足 (如果不需要可以註解掉)
            await message.reply("抱歉,我沒有權限修改你的暱稱", delete_after=5)
            
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
