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
        # 檢查成就資料是否存在
        # 立即發送「正在思考」的回應，讓使用者知道指令被接收了
        await interaction.response.defer(ephemeral=False) # ephemeral=False 表示所有人可見

        user_id_str = str(member.id) # 將 member.id 轉換為字符串，以便匹配字典鍵

        # 從 bot.user_achievements 獲取該成員的成就列表
        # 如果成員沒有任何成就，就返回一個空列表
        user_unlocked_names = self.bot.user_achievements.get(user_id_str, [])

        if not user_unlocked_names:
            # 如果沒有解鎖任何成就
            response_message = f"**{member.display_name}** 尚未解鎖任何成就喔！"
        else:
            # 如果有解鎖成就，將成就名稱列表轉換為字符串
            achievement_list_str = "\n".join([f"✨ {name}" for name in user_unlocked_names])
            response_message = f"**{member.display_name}** 已解鎖以下成就：\n{achievement_list_str}"

        # 使用 follow_up.send 傳送最終回應，因為之前使用了 defer
        await interaction.followup.send(response_message)
       
        
        
    


async def setup(bot: commands.Bot):
    await bot.add_cog(MyCommands(bot))