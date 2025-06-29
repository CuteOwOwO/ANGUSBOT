# cogs/backup_task.py

import discord
from discord.ext import commands, tasks
import json
import logging
import os
from io import BytesIO # <-- 新增這行，用於將資料作為檔案發送

logger = logging.getLogger(__name__)

# --- 定義成就資料檔案的路徑 ---
USER_ACHIEVEMENTS_FILE = os.path.join(
    os.path.dirname(__file__),
    'achievements',
    'user_achievements.json'
)

CONVERSATION_RECORDS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'conversation_records.json')


BACKUP_CHANNEL_ID = 1384915793783029792 # <--- 範例：BACKUP_CHANNEL_ID = 123456789012345678

class BackupTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hourly_backup.start()
        logger.info(f"BackupTask Cog 已載入。成就資料檔案路徑設定為：{USER_ACHIEVEMENTS_FILE}")

    def cog_unload(self):
        self.hourly_backup.cancel()
        logger.info("BackupTask Cog 已卸載，每小時備份任務已停止。")

    @tasks.loop(hours=1)
    async def hourly_backup(self):
        logger.info("=== 每小時成就資料備份任務啟動 ===")
        backup_data = None # 初始化為 None，如果讀取失敗就不會發送

        # --- 嘗試讀取 JSON 檔案 ---
        try:
            with open(USER_ACHIEVEMENTS_FILE, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            logger.info("--- 成功讀取 user_achievements.json。---")
            
        except FileNotFoundError:
            logger.error(f"錯誤：找不到成就資料檔案：{USER_ACHIEVEMENTS_FILE}。請確認路徑是否正確或檔案已建立。")
        except json.JSONDecodeError as e:
            logger.error(f"錯誤：解碼 JSON 檔案 {USER_ACHIEVEMENTS_FILE} 失敗: {e}。檔案可能損壞。")
            try:
                with open(USER_ACHIEVEMENTS_FILE, 'r', encoding='utf-8') as f:
                    corrupted_content = f.read()
                logger.error(f"損壞檔案的內容（前500字元）：\n{corrupted_content[:500]}...")
            except Exception as read_err:
                logger.error(f"無法讀取損壞檔案內容進行偵錯：{read_err}")
        except Exception as e:
            logger.error(f"讀取成就資料時發生未預期錯誤: {e}", exc_info=True)

        # --- 如果資料讀取成功，則發送到 Discord 頻道 ---
        if backup_data: 
            try:
                # 獲取 Discord 頻道物件
                channel = self.bot.get_channel(BACKUP_CHANNEL_ID)
                if not channel:
                    logger.error(f"錯誤：找不到 ID 為 {BACKUP_CHANNEL_ID} 的頻道。請檢查頻道 ID 是否正確或機器人是否有權限訪問該頻道。")
                    return # 如果找不到頻道，則中止本次發送

                # 將 JSON 數據轉換為字符串，並使用 indent=2 讓其格式化美觀，ensure_ascii=False 確保中文字元正常顯示
                json_string = json.dumps(backup_data, indent=2, ensure_ascii=False)
                
                # 使用 BytesIO 在記憶體中創建一個「檔案」物件，用於發送
                file_data = BytesIO(json_string.encode('utf-8'))
                
                # 獲取當前時間戳，用於檔案名稱
                timestamp = discord.utils.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"user_achievements_backup_{timestamp}.json"

                # 發送訊息和檔案到頻道
                await channel.send(
                    f"🤖 每小時成就資料備份：{timestamp}",
                    file=discord.File(file_data, filename=filename) # 將 BytesIO 包裝成 discord.File
                )
                logger.info(f"成就資料備份已成功發送到頻道 ID: {BACKUP_CHANNEL_ID}。檔案名：{filename}")

            except discord.HTTPException as e:
                # 處理 Discord API 相關的錯誤（如權限不足、頻道不存在等）
                logger.error(f"錯誤：發送備份到 Discord 頻道失敗: {e}。請檢查機器人是否有足夠的權限（發送訊息、上傳檔案）。", exc_info=True)
            except Exception as e:
                # 處理其他任何發送時的未預期錯誤
                logger.error(f"發送備份到 Discord 頻道時發生未預期錯誤: {e}", exc_info=True)
        else:
            logger.warning("未成功讀取到成就資料，本次備份任務未發送檔案到 Discord 頻道。")

        logger.info("=== 每小時成就資料備份任務結束 ===")
        
    @tasks.loop(hours=6)
    async def hourly_backup(self):
        logger.info("=== 每小時成就資料備份任務啟動 ===")
        backup_data = None # 初始化為 None，如果讀取失敗就不會發送

        # --- 嘗試讀取 JSON 檔案 ---
        try:
            with open(CONVERSATION_RECORDS_FILE, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            logger.info("--- 成功讀取 user_achievements.json。---")
            
        except FileNotFoundError:
            logger.error(f"錯誤：找不到成就資料檔案：{CONVERSATION_RECORDS_FILE}。請確認路徑是否正確或檔案已建立。")
        except json.JSONDecodeError as e:
            logger.error(f"錯誤：解碼 JSON 檔案 {CONVERSATION_RECORDS_FILE} 失敗: {e}。檔案可能損壞。")
            try:
                with open(CONVERSATION_RECORDS_FILE, 'r', encoding='utf-8') as f:
                    corrupted_content = f.read()
                logger.error(f"損壞檔案的內容（前500字元）：\n{corrupted_content[:500]}...")
            except Exception as read_err:
                logger.error(f"無法讀取損壞檔案內容進行偵錯：{read_err}")
        except Exception as e:
            logger.error(f"讀取成就資料時發生未預期錯誤: {e}", exc_info=True)

        # --- 如果資料讀取成功，則發送到 Discord 頻道 ---
        if backup_data: 
            try:
                # 獲取 Discord 頻道物件
                channel = self.bot.get_channel(BACKUP_CHANNEL_ID)
                if not channel:
                    logger.error(f"錯誤：找不到 ID 為 {BACKUP_CHANNEL_ID} 的頻道。請檢查頻道 ID 是否正確或機器人是否有權限訪問該頻道。")
                    return # 如果找不到頻道，則中止本次發送

                # 將 JSON 數據轉換為字符串，並使用 indent=2 讓其格式化美觀，ensure_ascii=False 確保中文字元正常顯示
                json_string = json.dumps(backup_data, indent=2, ensure_ascii=False)
                
                # 使用 BytesIO 在記憶體中創建一個「檔案」物件，用於發送
                file_data = BytesIO(json_string.encode('utf-8'))
                
                # 獲取當前時間戳，用於檔案名稱
                timestamp = discord.utils.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"user_achievements_backup_{timestamp}.json"

                # 發送訊息和檔案到頻道
                await channel.send(
                    f"🤖 每小時對話資料備份：{timestamp}",
                    file=discord.File(file_data, filename=filename) # 將 BytesIO 包裝成 discord.File
                )
                logger.info(f"對話資料備份已成功發送到頻道 ID: {BACKUP_CHANNEL_ID}。檔案名：{filename}")

            except discord.HTTPException as e:
                # 處理 Discord API 相關的錯誤（如權限不足、頻道不存在等）
                logger.error(f"錯誤：發送備份到 Discord 頻道失敗: {e}。請檢查機器人是否有足夠的權限（發送訊息、上傳檔案）。", exc_info=True)
            except Exception as e:
                # 處理其他任何發送時的未預期錯誤
                logger.error(f"發送備份到 Discord 頻道時發生未預期錯誤: {e}", exc_info=True)
        else:
            logger.warning("未成功讀取到成就資料，本次備份任務未發送檔案到 Discord 頻道。")

        logger.info("=== 每小時成就資料備份任務結束 ===")

    @hourly_backup.before_loop
    async def before_hourly_backup(self):
        logger.info("每小時成就資料備份任務等待 Bot 上線...")
        await self.bot.wait_until_ready()
        logger.info("Bot 已上線，每小時成就資料備份任務即將啟動。")

async def setup(bot):
    await bot.add_cog(BackupTask(bot))