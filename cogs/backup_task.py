# cogs/backup_task.py

import discord
from discord.ext import commands, tasks
import json
import logging
import os
from io import BytesIO

logger = logging.getLogger(__name__)

# --- 定義成就資料檔案的路徑 ---
USER_ACHIEVEMENTS_FILE = os.path.join(
    os.path.dirname(__file__),
    'achievements', # 假設成就檔案在 cogs/achievements/user_achievements.json
    'user_achievements.json'
)

# --- 定義對話紀錄檔案的路徑 ---
# 請根據您的實際檔案路徑調整這裡！
# 如果 conversation_records.json 和 user_achievements.json 在同一個 'achievements' 資料夾下，則保持不變。
# 如果 conversation_records.json 在另一個 'data' 資料夾下，例如 cogs/data/conversation_records.json，則應如下：
CONVERSATION_RECORDS_FILE = os.path.join(
    os.path.dirname(__file__),
    'achievements', # <--- 請確認這個路徑是否正確，如果您的 conversation_records.json 在 'data' 資料夾裡，這裡應該是 'data'
    'conversation_records.json'
)


BACKUP_CHANNEL_ID = 1384915793783029792 # <--- 您的備份頻道 ID

class BackupTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # --- 啟動兩個備份任務 ---
        self.hourly_achievement_backup.start() # 啟動成就備份任務
        self.hourly_conversation_backup.start() # 啟動對話紀錄備份任務

        logger.info(f"BackupTask Cog 已載入。")
        logger.info(f"成就資料檔案路徑設定為：{USER_ACHIEVEMENTS_FILE}")
        logger.info(f"對話紀錄檔案路徑設定為：{CONVERSATION_RECORDS_FILE}")

    def cog_unload(self):
        # --- 確保取消兩個備份任務 ---
        self.hourly_achievement_backup.cancel()
        self.hourly_conversation_backup.cancel()
        logger.info("BackupTask Cog 已卸載，所有備份任務已停止。")

    @tasks.loop(hours=1) # 每小時備份成就
    async def hourly_achievement_backup(self):
        logger.info("=== 每小時成就資料備份任務啟動 ===")
        # 從 self.bot 屬性中獲取成就數據（這是記憶體中的最新狀態）
        await self._perform_backup(USER_ACHIEVEMENTS_FILE, "成就資料", self.bot.user_achievements)
        logger.info("=== 每小時成就資料備份任務結束 ===")

    @tasks.loop(hours=6) # 每6小時備份對話紀錄
    async def hourly_conversation_backup(self):
        logger.info("=== 每小時對話紀錄資料備份任務啟動 ===")
        # 從 self.bot 屬性中獲取對話紀錄數據（這是記憶體中的最新狀態）
        await self._perform_backup(CONVERSATION_RECORDS_FILE, "對話紀錄", self.bot.conversation_histories_data)
        logger.info("=== 每小時對話紀錄資料備份任務結束 ===")

    # 通用的備份函式，處理檔案讀取、發送和錯誤處理
    async def _perform_backup(self, filepath, data_type_name, data_to_backup):
        channel = self.bot.get_channel(self.BACKUP_CHANNEL_ID)
        if not channel:
            logger.error(f"錯誤：備份頻道 ID {self.BACKUP_CHANNEL_ID} 無效或未找到。請檢查配置。")
            return

        # 檢查 data_to_backup 是否為空，而不是檢查檔案是否存在
        if not data_to_backup:
            logger.warning(f"警告：沒有 {data_type_name} 數據可備份（記憶體中的數據為空）。")
            return

        try:
            # 將記憶體中的數據轉換為 JSON 字串
            json_string = json.dumps(data_to_backup, indent=2, ensure_ascii=False)
            
            # 使用 BytesIO 在記憶體中創建一個「檔案」物件，用於發送
            file_data = BytesIO(json_string.encode('utf-8'))
            
            # 獲取當前時間戳，用於檔案名稱
            timestamp = discord.utils.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # 根據數據類型動態生成檔案名
            filename = f"{data_type_name.replace('資料', '').strip().lower()}_backup_{timestamp}.json" 
            # 例如 "成就_backup_..." 或 "對話紀錄_backup_..."

            # 發送訊息和檔案到頻道
            await channel.send(
                f"🤖 每小時 {data_type_name} 備份：{timestamp}",
                file=discord.File(file_data, filename=filename)
            )
            logger.info(f"{data_type_name} 備份已成功發送到頻道 ID: {self.BACKUP_CHANNEL_ID}。檔案名：{filename}")

        except discord.HTTPException as e:
            logger.error(f"錯誤：發送 {data_type_name} 備份到 Discord 頻道失敗: {e}。請檢查機器人是否有足夠的權限（發送訊息、上傳檔案）。", exc_info=True)
        except Exception as e:
            logger.error(f"發送 {data_type_name} 備份到 Discord 頻道時發生未預期錯誤: {e}", exc_info=True)

    @hourly_achievement_backup.before_loop
    @hourly_conversation_backup.before_loop # 確保兩個任務都在 bot ready 後才開始
    async def before_any_backup_loop(self): # 可以使用一個通用的 before_loop 函式
        await self.bot.wait_until_ready()
        logger.info("備份任務等待機器人上線...")

# Cog 檔案必須有一個 setup 函式，用來將 Cog 加入到機器人中
async def setup(bot):
    await bot.add_cog(BackupTask(bot))