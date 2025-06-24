import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import asyncio # 確保頂部有這個導入

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.all()
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="%", intents=intents)

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


# 成就檔案路徑
ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__), 'cogs' , 'achievements', 'normal_achievements.json')
USER_ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__), 'cogs' , 'achievements', 'user_achievements.json')

def load_achievements(file_path):
    """從 JSON 檔案載入成就定義。"""
    if not os.path.exists(file_path):
        print(f"警告: 成就定義檔案 '{file_path}' 不存在。")
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"錯誤: 解析成就定義檔案 '{file_path}' 失敗: {e}")
        return []
    except Exception as e:
        print(f"載入成就定義檔案 '{file_path}' 時發生錯誤: {e}")
        return []

def load_user_achievements(file_path):
    """從 JSON 檔案載入使用者已達成的成就記錄。"""
    if not os.path.exists(file_path):
        print(f"警告: 使用者成就記錄檔案 '{file_path}' 不存在。將創建新檔案。")
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"錯誤: 解析使用者成就記錄檔案 '{file_path}' 失敗: {e}。將初始化空記錄。")
        return {}
    except Exception as e:
        print(f"載入使用者成就記錄檔案 '{file_path}' 時發生錯誤: {e}。將初始化空記錄。")
        return {}



# 當機器人完成啟動
@bot.event
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    print("----- 載入 Cogs -----")

    # 載入成就資料和使用者成就記錄 (這是同步的函數調用，沒問題)
    bot.achievements_data = load_achievements(ACHIEVEMENTS_FILE)
    bot.user_achievements = load_user_achievements(USER_ACHIEVEMENTS_FILE)
    print(f"載入 {len(bot.achievements_data)} 個成就定義。")
    print(f"載入 {len(bot.user_achievements)} 個使用者成就記錄。")

    # 載入 cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"成功載入 {filename}")
            except Exception as e:
                print(f"無法載入 {filename}: {e}")
    print("----- Cogs 載入完成 -----")

    # 同步斜線指令
    try:
        synced = await bot.tree.sync()
        print(f"同步了 {len(synced)} 個斜線指令。")
    except Exception as e:
        print(f"同步斜線指令時發生錯誤: {e}")

    # 設定機器人狀態
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="大家聊天"),
        status=discord.Status.online
    )
 
    # (可選) 啟動訊息發送
    log_channel_id = 1384915793783029792
    log_channel = bot.get_channel(log_channel_id)
    # if log_channel:
    #    await log_channel.send(f"<@1382919972707369051> 姊姊早安，我是嘎嘎嘎!")

# Cog 管理指令
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

# 運行機器人 (這是 main.py 中唯一呼叫 asyncio.run() 的地方，透過 bot.run 隱式呼叫)
bot.run(TOKEN)