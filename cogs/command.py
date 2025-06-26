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
            if count >= 100: # 可以調整金級的門檻
                return "🏆" # 金牌圖示
            elif count >= 30:
                return "🥈" # 銀牌圖示 (雖然通常金、銀、銅是 1000, 100, 10。這裡我暫用 🥈 代表銀)
            elif count >= 5:
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
            if achievement_name != "total_achievement_count": # 確保不包含總成就計數
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
        await interaction.response.defer(ephemeral=False) # 設置 ephemeral=False 讓所有人看到

        loli_achievements = self.bot.load_loli_achievements_definitions()
        sexy_achievements = self.bot.load_sexy_achievements_definitions()

        # 準備一個列表來收集所有成就訊息
        messages_to_send = []
        i = 0 
        messages_to_send.append("==== 小貓版成就 ====")
        for achievement in loli_achievements:
            if i <= 9:
                messages_to_send.append(f"🌟 {achievement['name']}")
                i += 1
        i=0
        messages_to_send.append("\n==== 大貓貓版成就 ====") # 加一個換行讓分隔線更清晰
        for achievement in sexy_achievements:
            if i <= 9:
                i += 1
                messages_to_send.append(f"🌟 {achievement['name']}")

        # 將所有收集到的訊息組合成一個大的字串
        # 注意：Discord 訊息有字元限制 (通常是 2000 字元)，如果成就很多可能需要分段發送
        full_message_content = "\n".join(messages_to_send)

        if len(full_message_content) > 2000: # Discord 訊息字元限制
            chunks = [full_message_content[i:i+1900] for i in range(0, len(full_message_content), 1900)]
            for chunk in chunks:
                await interaction.followup.send(chunk, ephemeral=False)
        else:
            await interaction.followup.send(full_message_content, ephemeral=False)
            
    @discord.app_commands.command(name="世界排行", description="看看世界最奇怪的人們")
    async def world_ranking(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False) # 讓所有人看到排行

        try:
            self.bot.user_achievements = self.bot.load_user_achievements_data()
            print(f"[斜線指令 /世界排行] 重新載入使用者成就數據。")
        except Exception as e:
            print(f"[斜線指令 /世界排行錯誤] 載入使用者數據失敗：{e}")
            await interaction.followup.send(f"載入成就數據時發生錯誤：`{e}`", ephemeral=False)
            return

        leaderboard = []
        # 遍歷所有使用者的成就數據
        for user_id_str, user_data in self.bot.user_achievements.items():
            # 確保 user_id_str 是數字，並且有 'total_achievement_count' 欄位
            if user_id_str.isdigit(): # 確保是有效的用戶ID字串
                user_total_count = user_data.get('total_achievement_count', 0)
                if user_total_count > 0: # 只顯示有成就的用戶
                    leaderboard.append({'user_id': int(user_id_str), 'total_count': user_total_count})

        # 根據 total_count 進行降序排序
        leaderboard.sort(key=lambda x: x['total_count'], reverse=True)

        # 獲取前三名 (或更多，你可以調整[:3])
        if len(leaderboard) < 3:
            top_players = leaderboard[:len(leaderboard)]  # 如果少於3人，就取全部
        else:
            top_players = leaderboard[:3]

        if not top_players:
            await interaction.followup.send("目前還沒有人解鎖成就，排行榜是空的。", ephemeral=False)
            return

        '''# 建立排行榜訊息
        ranking_messages = ["=== 世界成就排行 ==="]
        for i, player in enumerate(top_players):
            user_id = player['user_id']
            total_count = player['total_count']
            
            # 嘗試獲取 Discord 使用者物件，以便顯示使用者名稱
            user_obj = None
            try:
                user_obj = await self.bot.fetch_user(user_id) # 這裡使用 fetch_user 確保能獲取到不在緩存中的用戶
            except discord.NotFound:
                user_obj = None # 如果用戶不存在，就保持為 None
            except Exception as e:
                print(f"[斜線指令 /世界排行錯誤] 無法獲取用戶 {user_id}：{e}")
                user_obj = None

            user_display_name = user_obj.display_name if user_obj else f"未知使用者 ({user_id})"
            
            ranking_messages.append(f"🎈**第 {i+1} 名**: {user_display_name} - 總成就次數：`{total_count}`🎈")

        ranking_messages.append("====================")

        full_ranking_message = "\n".join(ranking_messages)
        
        await interaction.followup.send(full_ranking_message, ephemeral=False)'''
        embed_description_lines = []
        trophy_emojis = ["🐘", "🐳", "🥈", "🥉"]
        for i, player in enumerate(top_players):
            user_id = player['user_id']
            total_count = player['total_count']
            
            user_obj = None
            try:
                user_obj = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                user_obj = None
            except Exception as e:
                print(f"[斜線指令 /世界排行錯誤] 無法獲取用戶 {user_id}：{e}")
                user_obj = None

            user_display_name = user_obj.display_name if user_obj else f"未知使用者 ({user_id})"
            
            # 根據名次選擇獎盃圖示
            if i < len(trophy_emojis):
                rank_emoji = trophy_emojis[i]
            else:
                rank_emoji = "🐳" # 其他名次使用這個圖示

            embed_description_lines.append(f"{rank_emoji} **第 {i+1} 名**: {user_display_name} - 總成就次數：`{total_count}`")

        embed = discord.Embed(
            title="🌎 世界成就排行",
            description="\n".join(embed_description_lines), # 將所有排名訊息放入 description
            color=discord.Color.gold() # 可以選擇你喜歡的顏色，例如金色
        )
        
        # 可選：設置一個縮圖或作者、頁腳等
        # 如果你有機器人的頭像 URL，可以用 embed.set_thumbnail(url=self.bot.user.avatar.url)
        # 如果你希望顯示是哪個機器人發的，可以加 footer
        embed.set_footer(text=f"統計日期: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M')}")
        await interaction.followup.send(embed=embed, ephemeral=False)



async def setup(bot: commands.Bot):
    await bot.add_cog(MyCommands(bot))