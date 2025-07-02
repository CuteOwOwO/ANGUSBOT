import discord
from discord.ext import commands, tasks
from datetime import datetime, time
import asyncio

class DailyReset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reset_time = time(hour=0, minute=0, second=0) 
        
        # 或者如果你想讓它每天在 Bot 啟動後等待24小時執行一次
        # @tasks.loop(hours=24)
        
        # 或者每天在特定時間執行
        # @tasks.loop(time=self.reset_time)
        self.daily_reset_task.start() # 啟動定時任務

    # 當 Cog 被卸載時，取消任務以避免資源洩漏
    def cog_unload(self):
        self.daily_reset_task.cancel()

    @tasks.loop(time=time(hour=0, minute=0, second=0)) # 設定每天 UTC 時間 0:00 執行
    # 如果要每天在 Bot 啟動後24小時循環，可以使用 @tasks.loop(hours=24)
    async def daily_reset_task(self):
        """
        每天執行一次的任務，用於重置所有用戶的狀態。
        """
        print(f"[{datetime.now()}] 每日重置任務開始執行...")

        # 清空所有用戶的狀態字典
        # 假設你的 bot.user_status 是一個字典，結構類似 {user_id: {"state": "...", ...}}
        # 這裡會遍歷並重置每個用戶的狀態，或者直接清空整個字典，取決於你的需求
        log_channel_id = 1384915793783029792  # <-- 替換為你的頻道 ID
        log_channel = self.bot.get_channel(log_channel_id)
        # 方法一：遍歷所有用戶並重置他們的狀態為 'idle'
        for user_id in list(self.bot.user_status.keys()): # 遍歷副本以避免在迭代時修改字典
            # 你可以選擇重置特定的狀態，而不是完全清空所有資訊
            if user_id in self.bot.user_guessing_times:
                self.bot.user_guessing_times[user_id] = 0  # 重置猜病次數
                await log_channel.send(f"[{datetime.now().strftime('%H:%M')}] 用戶 {user_id} 猜病次數已重置。")
            if user_id in self.bot.user_status:
                if self.bot.user_status[user_id].get("state") == "guessing":
                    self.bot.user_status[user_id]["state"] = "idle"
                    await log_channel.send(f"[{datetime.now().strftime('%H:%M')}] 用戶 {user_id} 狀態已重置為閒置。")
                
        self.bot.user_finish_guess = []  # 清空所有用戶的猜病狀態
        self.bot.user_signeveryday = []    
        
            
        print(f"[{datetime.now()}] 所有用戶猜病狀態已重置。")


        log_channel_id = 1384915793783029792  # <-- 替換為你的頻道 ID
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
           await log_channel.send(f"[{datetime.now().strftime('%H:%M')}] 用戶猜病狀態已重置。")
        else:
           print(f"無法找到 ID 為 {log_channel_id} 的日誌頻道。")
           
           

    @daily_reset_task.before_loop
    async def before_daily_reset_task(self):
        """
        在定時任務啟動前，等待 Bot 連線並準備好。
        """
        await self.bot.wait_until_ready()
        print("每日重置任務等待 Bot 連線完成...")

# Cog 檔案必須有一個 setup 函式
async def setup(bot):
    await bot.add_cog(DailyReset(bot))