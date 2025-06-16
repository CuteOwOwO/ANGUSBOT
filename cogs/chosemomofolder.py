import discord
from discord.ext import commands
import asyncio # 用於 TimeoutError

class ReactionHandlerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.EMOJI_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        # 這個 Cog 不再需要 momofoldernames 字典，因為它只處理選擇的數字索引
        # 中文名稱的處理將留給需要它的 Cog (例如抽卡 Cog)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        print(f"使用者 {user.display_name} 在訊息 {reaction.message.id} 上添加了反應 {reaction.emoji}")
        # 排除機器人本身的反應
        if user == self.bot.user:
            return
        
        user_id = user.id
        
        # 檢查使用者是否處於「等待選擇資料夾」的狀態，並且反應的訊息是我們發送的那條
        current_user_status_info = self.bot.user_status.get(user_id)

        # 確保狀態信息是字典，並且狀態匹配，且訊息ID匹配
        if isinstance(current_user_status_info, dict) and \
           current_user_status_info.get("state") == "waiting_chose_folder" and \
           current_user_status_info.get("message_id") == reaction.message.id:

            # 檢查反應的表情符號是否在我們預期的數字表情中
            if str(reaction.emoji) in self.EMOJI_NUMBERS:
                chosen_index = self.EMOJI_NUMBERS.index(str(reaction.emoji)) # 獲取表情符號的索引 (0-4)

                # 確保索引在我們實際發送的卡包數量範圍內
                chosen_folders_order = current_user_status_info.get("chosen_folders_order")
                
                # 只有當 chosen_folders_order 存在且索引有效時才處理
                if chosen_folders_order and 0 <= chosen_index < len(chosen_folders_order):
                    # 直接從 chosen_folders_order 中獲取使用者選擇的資料夾編號
                    selected_folder_number = chosen_folders_order[chosen_index] 
                    
                    display_name = self.bot.chosen_folder_names[user_id][chosen_index] if user_id in self.bot.chosen_folder_names and len(self.bot.chosen_folder_names[user_id]) > chosen_index else f"未知資料夾{selected_folder_number}"

                    # --- 更新使用者狀態：資料夾已選擇 ---
                    
                    self.bot.user_chosen_folder[user_id]["state"] = "folder_selected" # 更新狀態為資料夾已選擇
                    self.bot.user_chosen_folder[user_id]["selected_folder_number"] = selected_folder_number # 儲存選擇的資料夾編號
                    self.bot.user_chosen_folder[user_id]["selected_folder_name"] = display_name
                    self.bot.user_chosen_folder[user_id]["message_id"] = reaction.message.id # 儲存訊息ID以便後續操作
                    self.bot.user_chosen_folder[user_id]["message_channel_id"] = reaction.message.channel.id
                    self.bot.user_status[user_id]["last_message_id"] = reaction.message.id # 更新最後一條訊息ID
                    

                    print(f"使用者 {user.display_name} 選擇了資料夾編號 {selected_folder_number}，狀態更新為 'folder_selected'。")
                    
                    await reaction.message.channel.send(
                        f"你選擇了：**{display_name}**！現在可以去打手槍了，記得鎖門!!",
                        reference=reaction.message # 回覆到選擇訊息
                    )
                    self.bot.user_status[user_id]["state"] = "folder_selected" # 更新狀態為資料夾已選擇
                    print(f"使用者 {user.display_name} 選擇了卡包：{display_name} (編號: {selected_folder_number})")
                    
                    # --- 啟動初始抽卡流程 ---
                    momo_cog = self.bot.get_cog('sendselectedmomo') # 獲取 momo Cog 的實例
                    if momo_cog:
                        # 傳遞用戶ID和頻道物件，讓 momo Cog 知道在哪裡發送卡牌
                        await momo_cog.start_initial_draw(user_id, reaction.message.channel)
                    else:
                        print("錯誤: momo Cog 未載入，無法啟動初始抽卡流程。")
                        await reaction.message.channel.send("發生內部錯誤，無法啟動抽卡。請聯繫管理員。")
                        self.bot.user_status[user_id]["state"] = "idle" # 錯誤時重置狀態

                    # 清除反應，避免重複選擇或混亂
                    try:
                        await reaction.message.clear_reactions()
                    except discord.Forbidden:
                        print(f"沒有權限清除訊息 {reaction.message.id} 的反應。")
                    except discord.NotFound:
                        print(f"訊息 {reaction.message.id} 已被刪除，無法清除反應。")
                else:
                    await reaction.message.channel.send("無效的選擇，請點擊有效的表情符號。", reference=reaction.message)
            # 如果點擊的不是數字表情符號，且在選擇階段，則移除該反應
            elif reaction.message.id == current_user_status_info.get("message_id"):
                try:
                    await reaction.remove(user)
                except discord.Forbidden:
                    print(f"沒有權限移除使用者 {user.display_name} 在訊息 {reaction.message.id} 上的反應。")
                except discord.NotFound:
                    print(f"訊息 {reaction.message.id} 或反應已被刪除，無法移除。")
        
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        pass

# Cog 檔案必須有一個 setup 函式
async def setup(bot):
    await bot.add_cog(ReactionHandlerCog(bot))