# cogs/your_cog_file.py
import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone # <--- 新增導入這兩個
import json
import logging
import os
import asyncio
from . import image_generator
import random
async def save_conversation_data_local(data, file_path):
    """將對話紀錄保存到 JSON 檔案。在單獨的線程中執行阻塞的 I/O 操作。"""
    await asyncio.to_thread(_save_conversation_sync_local, data, file_path)

def _save_conversation_sync_local(data, file_path):
    """實際執行對話紀錄檔案保存的同步函數，供 asyncio.to_thread 調用。"""
    try:
        # 確保資料夾存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[mention Cog] 對話紀錄已保存到 '{file_path}'。")
        logging.info(f"[mention Cog] 對話紀錄已保存到 '{file_path}'。") # 增加日誌記錄
    except Exception as e:
        print(f"[mention Cog] 保存對話紀錄到 '{file_path}' 時發生錯誤: {e}")
        logging.error(f"[mention Cog] 保存對話紀錄到 '{file_path}' 時發生錯誤: {e}", exc_info=True) # 增加錯誤日誌記錄
        
SIGN_IN_FILE = os.path.join(os.path.dirname(__file__), 'sign_in.json') # 新增簽到檔案路徑
CONVERSATION_RECORDS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'conversation_records.json')



def load_json_prompt_history(file_name):
    current_dir = os.path.dirname(__file__)
    prompt_file_path = os.path.join(current_dir, 'prompts', file_name)
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            return json.load(f) # 使用 json.load()
    except FileNotFoundError:
        print(f"錯誤: JSON 提示檔案 '{prompt_file_path}' 未找到。請確保檔案存在。")
        # 返回一個默認或空的歷史，防止程式崩潰
        return [
            {"role": "user", "parts": ["你是一位樂於助人的 Discord 機器人，用友善、簡潔的方式回答使用者的問題。"]},
            {"role": "model", "parts": ["好的，我明白了，我將會用友善、簡潔的方式回答使用者的問題。"]}
        ]
    except json.JSONDecodeError as e:
        print(f"錯誤: 解析 JSON 提示檔案 '{prompt_file_path}' 失敗: {e}")
        return [
            {"role": "user", "parts": ["你是一位樂於助人的 Discord 機器人，用友善、簡潔的方式回答使用者的問題。"]},
            {"role": "model", "parts": ["好的，我明白了，我將會用友善、簡潔的方式回答使用者的問題。"]}
        ]
    except Exception as e:
        print(f"讀取 JSON 提示檔案 '{prompt_file_path}' 時發生未知錯誤: {e}")
        return [
            {"role": "user", "parts": ["你是一位樂於助人的 Discord 機器人，用友善、簡潔的方式回答使用者的問題。"]},
            {"role": "model", "parts": ["好的，我明白了，我將會用友善、簡潔的方式回答使用者的問題。"]}
        ]

class MyCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        
    @discord.app_commands.command(name="help", description="顯示機器人所有可用的指令和功能。")
    async def help_command(self, interaction: discord.Interaction):
        
        await interaction.response.defer(ephemeral=False) # 讓所有人看到幫助訊息

        embed = discord.Embed(
            title="🤖 小貓貓功能列表 🤖",
            description="以下是你可以使用的一些指令！",
            color=discord.Color.purple() # 你可以選擇任何你喜歡的顏色
        )

        # 設置縮圖（如果你的機器人有頭像，可以放上來）
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        # 添加欄位來列出指令
        
        # 添加你提供的新功能，並加上表情符號
        embed.add_field(
            name="🗣️ 和你說話! `(直接 @嘎嘎嘎)`", # 加上 "@貓貓" 提示使用者如何觸發
            value="可以把貓貓當成可愛一點的AI，或是把他訓(調)練(教)成你想要的樣子。",
            inline=False
        )
        
        embed.add_field(
            name="🧚‍♀️ 美少女變身!! `(關鍵字: 蘿莉/御姊)`", # 說明觸發關鍵字
            value="貓貓有兩種型態！可以用蘿莉以及御姊關鍵字觸發。",
            inline=False
        )
        
        embed.add_field(
            name="🌟 成就攻略系統",
            value="會根據貓貓的回答解鎖成就！",
            inline=False
        )
        
        embed.add_field(
            name="🖼️ 可愛貓貓圖片",
            value="解鎖成就時可以看到可愛貓貓~~",
            inline=False
        )
        
        embed.add_field(
            name="🏆 `/世界排行`",
            value="看看有什麼很閒又很厲害的人",
            inline=False
        )

        embed.add_field(
            name="🏅 `/查看成就 [成員]`",
            value="查看指定成員已解鎖的成就和解鎖次數。",
            inline=False
        )
        
        embed.add_field(
            name="🧠 猜病小遊戲", # 或許用腦袋或遊戲相關表情
            value="就猜病，但貓貓比較老實，有點太簡單。",
            inline=False
        )
        
        embed.add_field(
            name="📅 每日簽到", # 或許用腦袋或遊戲相關表情
            value="每天來看一下貓貓，簽到領取可愛圖片！",
            inline=False
        )
        
        embed.add_field(
            name="🎨 `/來看可愛的貓咪吧 [內容] [模式]`",
            value="使用 AI 根據你的描述生成圖片。\n`內容`: 你希望圖片呈現的內容 (英文)。\n`模式`: 選擇圖片風格 (`小貓版` 或 `大貓貓版`)。",
            inline=False
        )

        # 可以在底部添加一些額外的資訊
        embed.set_footer(text="更多功能陸續開發中，敬請期待！")
        await interaction.followup.send(embed=embed, ephemeral=False)

    @discord.app_commands.command(name="myid", description="顯示你的使用者 ID")
    async def my_id_command(self, interaction: discord.Interaction):
        """
        這個斜線指令會回覆執行者的 Discord 使用者 ID。
        """
        user_id = interaction.user.id
        user_name = interaction.user.display_name # 顯示名稱，如果是伺服器成員則為暱稱，否則為使用者名稱

        # 你可以選擇讓回覆只有執行者看得到 (ephemeral=True)
        await interaction.response.send_message(f"你的使用者 ID 是：`{user_id}` ({user_name})", ephemeral=False)
        
        
    @discord.app_commands.command(name="每日簽到領貓貓", description="不要忘記人家貓貓嘛")
    @discord.app_commands.choices(mode=[
        discord.app_commands.Choice(name="小貓版", value="loli"),
        discord.app_commands.Choice(name="大貓貓版", value="sexy")
    ])
    async def everyday_signin(self, interaction: discord.Interaction , mode : str):
        await interaction.response.defer(thinking=True, ephemeral=False) # 讓所有人在處理時看到機器人「正在思考...」

        logging.info(f"使用者 {interaction.user.display_name} ({interaction.user.id}) 每日簽到。")
        user_id = interaction.user.id
        user_id = str(interaction.user.id)
        
        if user_id in self.bot.user_signeveryday:
            await interaction.followup.send("你今天已經簽到過了！", ephemeral=True)
            return
        
        # 從 bot.sign_in_data 中獲取用戶的簽到數據
        # 如果用戶是第一次簽到，這裡會返回一個空的字典，之後會被填入預設值
        user_sign_in_data = self.bot.sign_in_data.get(user_id, {})
        today_utc = datetime.now(timezone.utc).date() 

        last_checkin_date_str = user_sign_in_data.get('last_checkin_date')
        checkin_streak = user_sign_in_data.get('checkin_streak', 0)
        total_checkins = user_sign_in_data.get('total_checkins', 0)
        
        
        if last_checkin_date_str:
            # 將儲存的日期字串轉換回日期物件以便比較
            last_checkin_date = datetime.strptime(last_checkin_date_str, "%Y-%m-%d").date()

            if last_checkin_date == today_utc:
                # 情況一：同天重複簽到
                response_text = "喵嗚~ 主人今天已經簽到過了喔！每天只能簽到一次呢！"
                await interaction.followup.send(response_text, ephemeral=False)
                return 
                
            elif last_checkin_date == today_utc - timedelta(days=1):
                # 情況二：連續簽到 (上次簽到是昨天)
                checkin_streak += 1
                total_checkins += 1
                user_sign_in_data['last_checkin_date'] = today_utc.strftime("%Y-%m-%d") # 更新為今天的日期
                user_sign_in_data['checkin_streak'] = checkin_streak
                user_sign_in_data['total_checkins'] = total_checkins
                response_text = f"喵！恭喜主人連續簽到 **{checkin_streak}** 天了！真是太棒了！"
            else:
                # 情況三：斷簽 (上次簽到不是昨天也不是今天)
                checkin_streak = 1 # 重置連續簽到天數
                total_checkins += 1
                user_sign_in_data['last_checkin_date'] = today_utc.strftime("%Y-%m-%d") # 更新為今天的日期
                user_sign_in_data['checkin_streak'] = checkin_streak
                user_sign_in_data['total_checkins'] = total_checkins
                response_text = f"喵嗚~ 主人今天簽到囉！是新的連續簽到第 **{checkin_streak}** 天！要繼續保持喔！"
        else:
            # 情況四：首次簽到
            checkin_streak = 1
            total_checkins = 1
            user_sign_in_data['last_checkin_date'] = today_utc.strftime("%Y-%m-%d") # 記錄今天的日期
            user_sign_in_data['checkin_streak'] = checkin_streak
            user_sign_in_data['total_checkins'] = total_checkins
            response_text = "喵！主人第一次簽到呢！歡迎您，這是您連續簽到第 **1** 天！"

        self.bot.sign_in_data[user_id] = user_sign_in_data
        
        # 保存簽到數據到檔案
        try:
            # 調用 command.py 中的 save_conversation_data_local 來保存簽到數據
            # 注意：這裡保存的是 self.bot.sign_in_data，並且檔案路徑是 SIGN_IN_FILE
            await save_conversation_data_local(self.bot.sign_in_data, SIGN_IN_FILE)
            logging.info(f"使用者 {user_id} 簽到數據已更新並保存到 {SIGN_IN_FILE}：{user_sign_in_data}")
        except Exception as e:
            logging.error(f"保存簽到數據失敗: {e}", exc_info=True)
            response_text += "\n(簽到數據保存失敗，請聯繫管理員。)"

        self.bot.user_signeveryday.append(user_id)
        prompt = "主人早安(搖著尾巴)今天過的順利嘛!!(喵喵喵) **設計一個貓娘打招呼的好看情景**"

        try:
            # 調用 image_generator.py 中的函數
            # 我們將用戶的 prompt 作為 conversation_history 傳入，讓 Gemini 根據它來生成詳細提示詞
            image_stream = await image_generator.generate_image_with_ai(
                conversation_history=prompt, # 用戶輸入的 prompt 作為對話歷史
                mode=mode,                   # 選擇的風格模式
                way="sigh_in",
                image_name=f"generated_by_{interaction.user.name}"
            )

            if image_stream:
                # 將 BytesIO 物件轉換為 discord.File
                picture = discord.File(image_stream, filename=image_stream.name)
                
                # 發送圖片到 Discord
                await interaction.followup.send(
                    content = response_text,
                    file=picture
                )
                logging.info(f"圖片已成功發送給使用者 {interaction.user.id}。")
            else:
                await interaction.followup.send("抱歉，圖片生成失敗，沒有收到有效的圖片數據。請檢查日誌了解詳情。", ephemeral=False)
                logging.error(f"圖片生成失敗：generate_image_with_ai 未返回圖片流。")

        except Exception as e:
            logging.error(f"在 /畫圖 指令中發生錯誤: {e}", exc_info=True)
            await interaction.followup.send(
                f"在生成圖片時發生了錯誤：`{e}`\n請稍後再試，或聯繫管理員。",
                ephemeral=False
            )

    
        
    @discord.app_commands.command(name="消除記憶", description="嘎嘎嘎會忘記你!!")
    async def reset(self, interaction: discord.Interaction):
        
        '''這個斜線指令會回覆執行者的 Discord 使用者 ID。'''
        user_id = interaction.user.id
        user_id_str = str(user_id) # 確保使用字串作為字典鍵

        # 斜槓指令需要先 defer 回應，因為操作可能需要一點時間
        # ephemeral=True 讓回應只對發送指令的使用者可見，保護隱私
        await interaction.response.defer(ephemeral=False) 

        logging.info(f"[clear_history] 使用者 {user_id_str} 請求清除對話歷史。")

        # 檢查 bot.conversation_histories_data 中是否有該使用者的記錄
        if user_id_str in self.bot.conversation_histories_data:
            try:
                # 重新載入初始 Prompt 的內容，以用於清空歷史
                # 這樣確保清空後，該模式的歷史會被重設回初始狀態
                initial_loli_prompt = load_json_prompt_history('normal.json')
                initial_sexy_prompt = load_json_prompt_history('sexy.json')

                # 清空該使用者所有模式的對話歷史，重置為初始 Prompt 的內容
                # 我們不刪除 user_id_str 的鍵，只是清空其 modes 裡面的歷史列表
                self.bot.conversation_histories_data[user_id_str]["modes"]["loli"] = initial_loli_prompt
                self.bot.conversation_histories_data[user_id_str]["modes"]["sexy"] = initial_sexy_prompt
                
                # 確保 current_mode 存在且合理，即使清空了也保持其當前模式
                if "current_mode" not in self.bot.conversation_histories_data[user_id_str]:
                    self.bot.conversation_histories_data[user_id_str]["current_mode"] = "loli" # 如果意外缺失，設為預設

                # === 關鍵修正：同步清除記憶體中該使用者的活動 ChatSession ===
                # 這是為了確保下次用戶對話時，會從已清空的歷史開始新的 ChatSession
                if user_id in self.bot.user_chats:
                    del self.bot.user_chats[user_id] # <-- 正確的做法是刪除這個鍵
                    logging.info(f"[clear_history] 清除使用者 {user_id} 在記憶體中的活動 ChatSession。")

                # === 關鍵修正：呼叫 save_conversation_data_local 將更改保存到文件 ===
                await save_conversation_data_local(self.bot.conversation_histories_data, CONVERSATION_RECORDS_FILE)
                logging.info(f"[clear_history] 使用者 {user_id_str} 的對話歷史已成功清除並保存到文件。")

                # 發送成功的訊息給使用者
                await interaction.followup.send(f"嘎嘎嘎已經忘記關於{interaction.user.display_name}的事情了!!", ephemeral=False)

            
            except Exception as e:
                # 錯誤處理
                logging.error(f"[clear_history] 清除使用者 {user_id_str} 歷史時發生錯誤: {e}", exc_info=False)
                await interaction.followup.send("清除對話紀錄時發生錯誤，請稍後再試。", ephemeral=False)
        else:
            # 如果該使用者根本沒有對話紀錄
            await interaction.followup.send("主人，您好像還沒有對話紀錄呢，不需要清空喔！", ephemeral=False)
        
       
        
        

    @discord.app_commands.command(name="userinfo", description="獲取指定使用者的 ID")
    @discord.app_commands.describe(member="要查詢的成員")
    async def user_info_command(self, interaction: discord.Interaction, member: discord.Member):
        """
        這個斜線指令可以獲取指定成員的 Discord 使用者 ID。
        """
        member_id = member.id
        member_name = member.display_name

        await interaction.response.send_message(f"{member_name} 的使用者 ID 是：`{member_id}`", ephemeral=False)
        
        
    @discord.app_commands.command(name="查看對話紀錄個數", description="超過200會把你刪掉喔!!")
    @discord.app_commands.describe(member="要查詢的成員")
    async def user_chat_number(self, interaction: discord.Interaction, member: discord.Member):
        """
        這個斜線指令可以獲取指定成員的 Discord 使用者 ID。
        """
        member_id = member.id
        member_name = member.display_name
        num_conversations = len(self.bot.user_chats[member_id].history)
        await interaction.response.send_message(f"{member_name} 目前有 {num_conversations} 條對話紀錄~。", ephemeral=False)
        

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
        
    @discord.app_commands.command(name="flipcoins", description="擲多個硬幣，並逐步顯示結果！")
    @discord.app_commands.describe(num_coins="要擲的硬幣數量 (1到10個)") # 新增參數描述
    async def flip_coins_command(self, interaction: discord.Interaction, num_coins: int = 5): # 新增 num_coins 參數，預設為 5
        await interaction.response.defer(ephemeral=False) # 先延遲回應，讓所有人看到機器人正在思考

        # 檢查輸入的硬幣數量是否在合理範圍內
        if not (1 <= num_coins <= 10): # 可以調整最大數量，例如最多10個，避免訊息過長
            await interaction.followup.send("請輸入一個介於 1 到 10 之間的硬幣數量。", ephemeral=True)
            return

        # 硬幣結果列表：(文字, 表情符號)
        results_map = {
            "正面": "🔴", # 紅色圓形代表正面
            "反面": "⚫"  # 黑色圓形代表反面
        }
        
        all_flips_emojis = [] # 用來儲存所有擲出硬幣的表情符號
        initial_message = "🪙 貓貓把硬幣往上丟~..."
        
        await interaction.edit_original_response(content=initial_message)
        await asyncio.sleep(1.0) # 初始等待

        # num_coins_to_flip = 5 # 這一行現在由參數傳入，不需要固定了
        cnt = 0
        for i in range(num_coins): # 使用 num_coins 參數作為迴圈次數
            # 隨機選擇硬幣結果
            is_heads = random.choice([True, False])
            
            if is_heads:
                current_flip_emoji = "🔴"
            else:
                current_flip_emoji = "⚫"
            
            
            all_flips_emojis.append(current_flip_emoji) # 將新的硬幣結果添加到列表中

            # 構建當前要顯示的訊息
            current_display = "🪙 硬幣結果:\n" 
            for cnt , j in enumerate(all_flips_emojis):
                current_display += f"{j} "
                if cnt%3==2 :
                    current_display += "\n"
                    
            await interaction.edit_original_response(content=current_display)
            await asyncio.sleep(1.5) # 每次新增後延遲 1.5 秒

        final_count_heads = all_flips_emojis.count(results_map["正面"])
        final_count_tails = all_flips_emojis.count(results_map["反面"])

        final_summary_message = (
            f"最終結果：共擲出 {num_coins} 個硬幣。\n" # 使用 num_coins
            f"正面 (🔴) 有 {final_count_heads} 個，反面 (⚫) 有 {final_count_tails} 個。\n"
            f"總覽: {' '.join(all_flips_emojis)}"
        )
        
        await interaction.edit_original_response(content=final_summary_message)
        logging.info(f"結果是 {final_count_heads} 正面, {final_count_tails} 反面。")

        
        
    @discord.app_commands.command(name="成就列表", description="看看有甚麼成就吧!!")
    async def achievements_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False) # 設置 ephemeral=False 讓所有人看到

        loli_achievements = self.bot.load_loli_achievements_definitions()
        sexy_achievements = self.bot.load_sexy_achievements_definitions()

        # 準備一個列表來收集所有成就訊息
        messages_to_send = []
        i = 0 
        messages_to_send.append("==== 小貓版成就 (部分) ====")
        for achievement in loli_achievements:
            if i <= 6:
                messages_to_send.append(f"🌟 {achievement['name']}")
                i += 1
        i=0
        messages_to_send.append("\n==== 大貓貓版成就 (部分) ====") # 加一個換行讓分隔線更清晰
        for achievement in sexy_achievements:
            if i <= 6:
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
        trophy_emojis = ["🐘", "🐳", "🦜", "🐑","🦜"]
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
        '''if self.bot.user and self.bot.user.avatar: # 確保機器人用戶和頭像存在
            embed.set_thumbnail(url=self.bot.user.avatar.url)'''
        taiwan_tz = timezone(timedelta(hours=8))
        # 獲取當前 UTC 時間並轉換為 UTC+8
        now_taiwan = datetime.now(taiwan_tz)
        
        embed.set_footer(text=f"統計日期: {now_taiwan.strftime('%Y-%m-%d %H:%M')}")
        await interaction.followup.send(embed=embed, ephemeral=False)
        
        
        
    @discord.app_commands.command(name="來看可愛的貓咪吧", description="使用AI生成圖片！")
    @discord.app_commands.describe(
        prompt="輸入你希望圖片呈現的內容（英文）",
        mode="選擇圖片風格（loli/sexy）"
    )
    @discord.app_commands.choices(mode=[
        discord.app_commands.Choice(name="小貓版", value="loli"),
        discord.app_commands.Choice(name="大貓貓版", value="sexy")
    ])
    async def draw_image_command(self, interaction: discord.Interaction, prompt: str, mode: str = "loli"):
        await interaction.response.defer(thinking=True, ephemeral=False) # 讓所有人在處理時看到機器人「正在思考...」

        logging.info(f"使用者 {interaction.user.display_name} ({interaction.user.id}) 請求畫圖，Prompt: '{prompt}', Mode: '{mode}'")

        try:
            # 調用 image_generator.py 中的函數
            # 我們將用戶的 prompt 作為 conversation_history 傳入，讓 Gemini 根據它來生成詳細提示詞
            image_stream = await image_generator.generate_image_with_ai(
                conversation_history=prompt, # 用戶輸入的 prompt 作為對話歷史
                mode=mode,                   # 選擇的風格模式
                way="command",
                image_name=f"generated_by_{interaction.user.name}"
            )

            if image_stream:
                # 將 BytesIO 物件轉換為 discord.File
                picture = discord.File(image_stream, filename=image_stream.name)
                
                # 發送圖片到 Discord
                await interaction.followup.send(
                    file=picture
                )
                logging.info(f"圖片已成功發送給使用者 {interaction.user.id}。")
            else:
                await interaction.followup.send("抱歉，圖片生成失敗，沒有收到有效的圖片數據。請檢查日誌了解詳情。", ephemeral=False)
                logging.error(f"圖片生成失敗：generate_image_with_ai 未返回圖片流。")

        except Exception as e:
            logging.error(f"在 /畫圖 指令中發生錯誤: {e}", exc_info=True)
            await interaction.followup.send(
                f"在生成圖片時發生了錯誤：`{e}`\n請稍後再試，或聯繫管理員。",
                ephemeral=False
            )
            
            
    



async def setup(bot: commands.Bot):
    await bot.add_cog(MyCommands(bot))