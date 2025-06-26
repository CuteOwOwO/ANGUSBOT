# cogs/your_cog_file.py
import discord
from discord.ext import commands

class MyCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="myid", description="顯示你的使用者 ID")
    async def my_id_command(self, interaction: discord.Interaction):
        """
        這個斜線指令會回覆執行者的 Discord 使用者 ID。
        """
        user_id = interaction.user.id
        user_name = interaction.user.display_name # 顯示名稱，如果是伺服器成員則為暱稱，否則為使用者名稱

        # 你可以選擇讓回覆只有執行者看得到 (ephemeral=True)
        await interaction.response.send_message(f"你的使用者 ID 是：`{user_id}` ({user_name})", ephemeral=False)
        
    @discord.app_commands.command(name="重製對話", description="記憶消失術!!")
    async def reset(self, interaction: discord.Interaction):
        """
        這個斜線指令會回覆執行者的 Discord 使用者 ID。
        """
        user_id = interaction.user.id
        if user_id in self.bot.user_chats:
            del self.bot.user_chats[user_id]
        
        await interaction.response.send_message(f"嘎嘎嘎已經忘記關於{interaction.user.display_name}的事情了!!", ephemeral=False)


    @discord.app_commands.command(name="userinfo", description="獲取指定使用者的 ID")
    @discord.app_commands.describe(member="要查詢的成員")
    async def user_info_command(self, interaction: discord.Interaction, member: discord.Member):
        """
        這個斜線指令可以獲取指定成員的 Discord 使用者 ID。
        """
        member_id = member.id
        member_name = member.display_name

        await interaction.response.send_message(f"{member_name} 的使用者 ID 是：`{member_id}`", ephemeral=False)
        
    @discord.app_commands.command(name="greet", description="向某人打招呼！")
    @discord.app_commands.describe(member="要打招呼的成員") # 為參數添加描述
    async def greet(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_message(f"喵喵喵你好!!{member.mention}！")
        
    @discord.app_commands.command(name="查看成就", description="看看大家的成就吧！")
    @discord.app_commands.describe(member="要打查看的成員") # 為參數添加描述
    async def see_achievements(self, interaction: discord.Interaction, member: discord.Member):
        
        await interaction.response.defer(ephemeral=False) # ephemeral=False 表示所有人可見
        
        try:
            self.bot.user_achievements = self.bot.load_user_achievements_data() # <--- 保持這行不變，確保用戶數據最新
        except Exception as e:
            print(f"[斜線指令 /查看成就錯誤] 載入成就定義失敗：{e}")
            await interaction.response.send_message(f"載入成就定義時發生錯誤：`{e}`", ephemeral=False)
            return

        user_id_str = str(member.id) # 將 member.id 轉換為字符串，以便匹配字典鍵

        # 從 bot.user_achievements 獲取該成員的成就列表
        # 如果成員沒有任何成就，就返回一個空列表
        user_achievements_data = self.bot.user_achievements.get(user_id_str, {})
        
        
        def get_badge_emoji(count):
            if count >= 1000: # 可以調整金級的門檻
                return "🏆" # 金牌圖示
            elif count >= 100:
                return "🥈" # 銀牌圖示 (雖然通常金、銀、銅是 1000, 100, 10。這裡我暫用 🥈 代表銀)
            elif count >= 10:
                return "🥉" # 銅牌圖示 (這裡我暫用 🥉 代表銅)
            elif count >= 1: # 只要有一次就顯示一個基本圖示
                return "✨" # 初始成就圖示
            return "" # 如果次數是0或負數，則不顯示

        if not user_achievements_data:
            # 如果沒有解鎖任何成就
            response_message = f"**{member.display_name}** 尚未解鎖任何成就喔！"
            return await interaction.followup.send(response_message, ephemeral=False)
        
        achievements_list = []
        for achievement_name, count in user_achievements_data.items():
            badge_emoji = get_badge_emoji(count) # <--- 調用函數獲取圖示
            achievements_list.append(f"{badge_emoji} **{achievement_name}** (解鎖了 {count} 次)")
        
        # 建立嵌入式訊息
        embed = discord.Embed(
            title=f"{member.display_name} 的成就",
            description="\n".join(achievements_list) if achievements_list else "你目前還沒有解鎖任何成就。",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        await interaction.followup.send(embed=embed, ephemeral=False)
        
        
        @discord.app_commands.command(name="成就列表", description="看看有甚麼成就吧!!")
        async def achievements_list(self, interaction: discord.Interaction):
            loli_achievements = self.bot.load_loli_achievements_definitions()
            sexy_achievements = self.bot.load_sexy_achievements_definitions()
            await interaction.response.send_message(f"小貓版成就~", ephemeral=False)
            for achievement in loli_achievements:
                if "小貓學壞了" not in achievement['name'] and "小貓討厭你" not in achievement['name']:
                    await interaction.response.send_message(f"🌟{achievement['name']}", ephemeral=False)
                    
            await interaction.response.send_message(f"大貓貓版成就~", ephemeral=False)
            for achievement in sexy_achievements:
                if "極致挑戰" not in achievement['name'] and "不悅凝視：冰冷警告" not in achievement['name']:
                    await interaction.response.send_message(f"🌟{achievement['name']}", ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(MyCommands(bot))