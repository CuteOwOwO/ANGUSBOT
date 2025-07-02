import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import logging # <-- 確保有導入 logging
from types import MethodType # <-- 新增這行

logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.all()
intents.reactions = True
intents.members = True

# 請將 YOUR_DISCORD_USER_ID 替換成你自己的 Discord 使用者 ID (一串數字)
# 獲取 Discord ID 的方法：在 Discord 設定中啟用「開發者模式」，然後在你的使用者名稱上右鍵點擊，選擇「複製 ID」。
bot = commands.Bot(command_prefix="%", intents=intents, owner_id = 852760898216656917) # <--- 修改這行，加入 owner_id

# 初始化 bot 屬性 (這些可能在其他 Cog 中被用到)
bot.user_status = {}
bot.user_chosen_folder = {}
bot.chosen_folder_names = {}
bot.everyday_symptom = {}
bot.user_guessing_times = {}
bot.user_finish_guess = []
bot.user_chats = {}
bot.user_checkpoint_loli = {}
bot.user_checkpoint_sexy = {}
bot.user_which_talkingmode = {} 
bot.user_signeveryday = []


# ====================================================================
# 新增區塊：定義 JSON 檔案路徑和通用的載入函數
# (已移除儲存函數 _save_json_data_internal 及其綁定)
# ====================================================================

# JSON 檔案路徑定義 (確保路徑正確)
LOLI_ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__), 'cogs' , 'achievements', 'normal_achievements.json') # <--- 修改這個變數名稱
USER_ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__), 'cogs' , 'achievements', 'user_achievements.json')
SEXY_ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__), 'cogs' , 'achievements', 'sexy_achievements.json')   # <--- 新增御姊版成就檔案路徑
CONVERSATION_RECORDS_FILE = os.path.join(os.path.dirname(__file__), 'cogs' , 'data', 'conversation_records.json') # <-- 新增這行

# 通用的 JSON 載入函數 (用於載入不同結構的 JSON 檔案)
def _load_json_data_internal(file_path, default_value): # <--- 這是唯一一個載入函數
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"警告: 檔案未找到 {file_path}，初始化為預設值。")
        return default_value
    except json.JSONDecodeError as e:
        print(f"錯誤: 解碼 JSON 檔案 {file_path} 失敗: {e}")
        return default_value
    except Exception as e:
        print(f"讀取 JSON 檔案 {file_path} 時發生未知錯誤: {e}")
        return default_value

bot.load_loli_achievements_definitions = lambda: _load_json_data_internal(LOLI_ACHIEVEMENTS_FILE, []) # <--- 改名並使用 LOLI_ACHIEVEMENTS_FILE

# 載入御姊版成就定義 (sexy_achievements.json)，預設為空列表
bot.load_sexy_achievements_definitions = lambda: _load_json_data_internal(SEXY_ACHIEVEMENTS_FILE, []) # <--- 新增這行，載入御姊版成就

# 載入用戶成就數據 (user_achievements.json)，預設為空字典
bot.load_user_achievements_data = lambda: _load_json_data_internal(USER_ACHIEVEMENTS_FILE, {})


bot.loli_achievements_definitions = bot.load_loli_achievements_definitions() # <--- 載入蘿莉版成就
bot.sexy_achievements_definitions = bot.load_sexy_achievements_definitions() # <--- 載入御姊版成就
bot.user_achievements = bot.load_user_achievements_data()

# ====================================================================
# 結束新增區塊
# ====================================================================


# 當機器人完成啟動
@bot.event
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    print("----- 載入 Cogs -----")
    bot.conversation_histories_data = _load_json_data_internal(CONVERSATION_RECORDS_FILE, {}) # <-- 新增這行
    logging.info(f"對話紀錄數據已載入到機器人記憶中。共有 {len(bot.conversation_histories_data)} 個用戶的紀錄。") # <-- 調整日誌訊息

    logging.info(f"載入 {len(bot.loli_achievements_definitions)} 個蘿莉版成就定義。") # <--- 新增或替換
    logging.info(f"載入 {len(bot.sexy_achievements_definitions)} 個御姊版成就定義。")   # <--- 新增
    logging.info(f"載入 {len(bot.user_achievements)} 個使用者成就記錄。")

    # 載入 cogs (這部分保持不變)
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"成功載入 {filename}")
            except Exception as e:
                print(f"無法載入 {filename}: {e}")
    print("----- Cogs 載入完成 -----")

    # 同步斜線指令 (這部分保持不變)
    try:
        synced = await bot.tree.sync()
        print(f"同步了 {len(synced)} 個斜線指令。")
    except Exception as e:
        print(f"同步斜線指令時發生錯誤: {e}")

    # 設定機器人狀態 (這部分保持不變)
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="大家聊天"),
        status=discord.Status.online
    )
 
    # (可選) 啟動訊息發送 (這部分保持不變)
    # log_channel_id = 1384915793783029792
    # log_channel = bot.get_channel(log_channel_id)
    # if log_channel:
    #    await log_channel.send(f"<@1382919972707369051> 姊姊早安，我是嘎嘎嘎!")

# Cog 管理指令 (這部分保持不變)
@bot.command()
async def load(ctx, extension):
    try:
        await bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'已載入 {extension}。')
    except Exception as e:
        await ctx.send(f'無法載入 {extension}: {e}')

@bot.command()
async def unload(ctx, extension):
    try:
        await bot.unload_extension(f'cogs.{extension}')
        await ctx.send(f'已卸載 {extension}。')
    except Exception as e:
        await ctx.send(f'無法卸載 {extension}: {e}')

@bot.command()
async def reload(ctx, extension):
    try:
        await bot.reload_extension(f'cogs.{extension}')
        await ctx.send(f'已重新載入 {extension}。')
    except Exception as e:
        await ctx.send(f'無法重新載入 {extension}: {e}')

# ====================================================================
# 新增區塊：手動重新載入成就定義的指令 (可選，但建議保留作為備用管理指令)
# ====================================================================
@bot.command(name="reload_achievements")
@commands.is_owner()
async def reload_achievements_command(ctx):
    """
    重新載入成就定義資料檔案 (normal_achievements.json)。
    這個指令只能由機器人擁有者在 Discord 中使用。
    使用方法：在 Discord 頻道中輸入 %reload_achievements
    """
    try:
        bot.loli_achievements_definitions = bot.load_loli_achievements_definitions() # <--- 重新載入蘿莉版
        bot.sexy_achievements_definitions = bot.load_sexy_achievements_definitions() # <--- 重新載入御姊版
        await ctx.send("✅ 所有成就定義資料已成功重新載入！") # <--- 更新訊息
        print(f"[管理員] 成就定義檔案已重新載入。")
    except Exception as e:
        await ctx.send(f"❌ 重新載入成就定義資料失敗：`{e}`")
        print(f"[管理員錯誤] 重新載入成就定義資料失敗：{e}")
# ====================================================================
# 結束新增區塊
# ====================================================================

# 運行機器人 (保持不變)
bot.run(TOKEN)