import discord
from discord.ext import commands
import asyncio

# --- 配置區塊 START ---
# 伺服器 ID
TARGET_GUILD_ID = 1421064550878412841 

SETUP_CHANNEL_ID = 1422873779826200679 
 AUTHORIZED_USER_ID = 852760898216656917

# 組別、身分組 ID、對應表情符號、以及私密頻道 ID 的映射
# 頻道 ID 部分，您需要手動創建或確認這些組別對應的專屬文字頻道 ID
# 如果您不想讓 Bot 自動加入頻道，可以將 'channel_id' 設為 None
ROLE_CONFIG = {
    # '組別名稱': {
    #     'role_id': 身分組ID, 
    #     'emoji': '表情符號', 
    #     'channel_id': 專屬頻道ID 
    # }
    "採買組": {
        'role_id': 1421067572115410944, 
        'emoji': '🛒', 
        'channel_id': 1421067572115410944  # 範例: 請替換為採買組專屬頻道 ID, 或設為 None
    },
    "美宣組": {
        'role_id': 1421067624711848019, 
        'emoji': '🎨', 
        'channel_id': 1421067624711848019  # 範例: 請替換為美宣組專屬頻道 ID, 或設為 None
    },
    "製作組": {
        'role_id': 1421067664016670720, 
        'emoji': '🛠️', 
        'channel_id': 1421067664016670720
    },
    "財務組": {
        'role_id': 1421067710217064468, 
        'emoji': '💰', 
        'channel_id': 1421067710217064468
    },
    "公關組": {
        'role_id': 1421067794497409064, 
        'emoji': '🗣️', 
        'channel_id': 1421067794497409064
    },
}
# --- 配置區塊 END ---


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 儲存 Bot 已經發送的組別訊息 ID，以便監聽反應時檢查
        # 結構: {訊息ID: '組別名稱'}
        self.monitored_messages = {}
        # 反向映射: {表情符號: '組別名稱'}
        self.emoji_to_group = {config['emoji']: group for group, config in ROLE_CONFIG.items()}


   # 確保 is_authorized_user 與 __init__ 保持相同的縮進，作為 Cog 的方法
    def is_authorized_user(self, ctx):
        # 假設 AUTHORIZED_USER_ID 已在檔案開頭的配置區塊定義
        # 注意：這裡假設 AUTHORIZED_USER_ID 是在 Cog 外部定義的全局變數
        # 如果是 Cog 內部變數，則需要 self.AUTHORIZED_USER_ID
        return ctx.author.id == AUTHORIZED_USER_ID
    
    @commands.command(name="setup_roles", aliases=['發布組別'])
    # *** 關鍵修改：用自訂檢查取代管理員權限檢查 ***
    @commands.check(is_authorized_user) 
    async def setup_roles_message(self, ctx):
        """
        發送所有組別的訊息，並自動加上反應。
        僅限特定用戶使用 (ID: 852760898216656917)。
        """
        if ctx.channel.id != SETUP_CHANNEL_ID:
            await ctx.send(f"請在正確的設置頻道 (<#{SETUP_CHANNEL_ID}>) 中使用此指令。", delete_after=10)
            return

        await ctx.send("正在發布組別選擇訊息，請稍候...")

        for group_name, config in ROLE_CONFIG.items():
            role_id = config['role_id']
            emoji = config['emoji']
            
            # 建立訊息內容
            role = ctx.guild.get_role(role_id)
            message_content = (
                f"**請點擊 {emoji} 以加入 [{group_name}]**\n"
                f"你將會獲得 <@&{role_id}> 身分組，並能看見相應頻道。"
            )
            
            try:
                # 發送訊息
                message = await ctx.send(message_content)
                # 加上反應
                await message.add_reaction(emoji)
                
                # 記錄訊息 ID 以供監聽
                self.monitored_messages[message.id] = group_name
                print(f"已發布並監聽 {group_name} 訊息: {message.id}")
                
            except discord.Forbidden:
                await ctx.send("錯誤: 我沒有權限在頻道中發送訊息或新增反應。", delete_after=10)
                return
            except Exception as e:
                await ctx.send(f"發送 {group_name} 訊息時發生錯誤: {e}", delete_after=10)
                
        await ctx.send("✅ 所有組別選擇訊息已發布並設置完成！", delete_after=10)
        
    @setup_roles_message.error
    async def setup_roles_error(self, ctx, error):
        # 處理指令權限錯誤（即非授權用戶嘗試使用）
        if isinstance(error, commands.CheckFailure):
            await ctx.send("你沒有權限執行此指令。", delete_after=5)
        # 如果是 Bot 找不到指令參數等其他錯誤，會由 discord.py 內建處理


    ## 2. 監聽反應事件 (新增)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # 忽略 Bot 自己的反應
        if payload.user_id == self.bot.user.id:
            return
            
        # 檢查是否為我們監聽的訊息
        if payload.message_id not in self.monitored_messages:
            return

        # 檢查是否為目標伺服器
        if payload.guild_id != TARGET_GUILD_ID:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        # 獲取成員物件
        member = guild.get_member(payload.user_id)
        if not member:
            return

        # 轉換表情符號為字串格式
        emoji_str = str(payload.emoji)
        
        # 根據表情符號找到組別名稱
        group_name = self.emoji_to_group.get(emoji_str)

        # 確保表情符號和組別名稱對應正確
        if group_name and group_name == self.monitored_messages[payload.message_id]:
            config = ROLE_CONFIG[group_name]
            role_id = config['role_id']
            channel_id = config['channel_id']
            
            # 獲取身分組物件
            role = guild.get_role(role_id)
            
            if role:
                try:
                    # 賦予身分組
                    await member.add_roles(role, reason=f"透過反應加入 {group_name}")
                    print(f"已給予 {member.name} {group_name} 身分組")
                    
                    # 處理頻道存取權 (如果配置了頻道 ID)
                    if channel_id:
                        channel = guild.get_channel(channel_id)
                        if channel and isinstance(channel, discord.TextChannel):
                            # 增加用戶對該頻道的存取權限 (覆蓋)
                            await channel.set_permissions(
                                member, 
                                read_messages=True, 
                                send_messages=True
                            )
                            print(f"已授予 {member.name} 存取 {channel.name} 頻道")
                        else:
                            print(f"警告: 找不到 ID 為 {channel_id} 的頻道或它不是文字頻道。")
                            
                    # 可選: 發送私訊通知 (建議)
                    try:
                        await member.send(f"✅ 你已成功加入 **{group_name}**！你現在擁有 <@&{role_id}> 身分組。")
                    except discord.Forbidden:
                        print(f"無法私訊 {member.name}")

                except discord.Forbidden:
                    print(f"Bot 權限不足，無法給予 {member.name} 身分組或設置頻道權限。")
                except Exception as e:
                    print(f"處理反應事件時發生錯誤: {e}")
                    
        else:
            # 如果用戶按了非預期的表情符號，將其移除
            # 需要先獲取訊息物件
            channel = self.bot.get_channel(payload.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(payload.message_id)
                    await message.remove_reaction(payload.emoji, member)
                except Exception as e:
                    print(f"移除非預期反應時發生錯誤: {e}")


    ## 3. 監聽反應事件 (移除) - 可選，用於移除身分組和頻道存取權

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        # 檢查是否為我們監聽的訊息
        if payload.message_id not in self.monitored_messages:
            return

        # 檢查是否為目標伺服器
        if payload.guild_id != TARGET_GUILD_ID:
            return
            
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        # 獲取成員 ID (注意 on_raw_reaction_remove 不直接提供 member 物件)
        member = guild.get_member(payload.user_id)
        if not member:
            return

        emoji_str = str(payload.emoji)
        group_name = self.emoji_to_group.get(emoji_str)

        if group_name and group_name == self.monitored_messages[payload.message_id]:
            config = ROLE_CONFIG[group_name]
            role_id = config['role_id']
            channel_id = config['channel_id']
            
            role = guild.get_role(role_id)
            
            if role:
                try:
                    # 移除身分組
                    await member.remove_roles(role, reason=f"透過移除反應退出 {group_name}")
                    print(f"已從 {member.name} 移除 {group_name} 身分組")
                    
                    # 處理頻道存取權 (如果配置了頻道 ID)
                    if channel_id:
                        channel = guild.get_channel(channel_id)
                        if channel and isinstance(channel, discord.TextChannel):
                            # 移除用戶對該頻道的權限覆蓋 (使其繼承頻道的預設權限)
                            await channel.set_permissions(member, overwrite=None)
                            print(f"已移除 {member.name} 對 {channel.name} 頻道的存取權限")

                    # 可選: 私訊通知
                    try:
                        await member.send(f"❌ 你已成功退出 **{group_name}**。")
                    except discord.Forbidden:
                        pass

                except discord.Forbidden:
                    print(f"Bot 權限不足，無法移除 {member.name} 身分組或設置頻道權限。")
                except Exception as e:
                    print(f"處理移除反應事件時發生錯誤: {e}")


# Cog 檔案必須有一個 setup 函式
async def setup(bot):
    # 確保 Bot 開啟了必要的 Intention (intent)
    # 為了 on_raw_reaction_add/remove 能正確運作，Bot 需要擁有 Intents.reactions
    # 為了 get_member/add_roles 能正確運作，Bot 需要擁有 Intents.members 
    # (如果沒有，請檢查您的主程式配置)
    await bot.add_cog(ReactionRoles(bot))
