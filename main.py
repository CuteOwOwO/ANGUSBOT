# 導入Discord.py模組
import discord
# 導入commands指令模組
from discord.ext import commands
import os # 導入 os 模組，用於讀取資料夾中的檔案
from dotenv import load_dotenv
import json # 導入 json 模組，用於讀取和寫入 JSON 檔案


load_dotenv()  # 載入 .env 檔案中的環境變數
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
# intents是要求機器人的權限
intents = discord.Intents.all()
intents.reactions = True       
intents.members = True 


# command_prefix是前綴符號，可以自由選擇($, #, &...)
bot = commands.Bot(command_prefix = "%", intents = intents)
bot.user_status = {}  # 用於存儲使用者的狀態
bot.user_chosen_folder = {}  # 用於存儲使用者選擇的資料夾
bot.chosen_folder_names = {}  # 用於存儲資料夾名稱
bot.last_message_id = {}
bot.user_status = {}  # 用於存儲使用者狀態
bot.user_finish_guess = []  # 用於存儲使用者猜病狀態
bot.everyday_symptom = {}
bot.user_guessing_times = {}
bot.user_chats = {}
bot.user_checkpoint_loli = {}
bot.user_checkpoint_sexy = {}

ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__), 'cogs','achievements', 'normal_achievement.json')
USER_ACHIEVEMENTS_FILE = os.path.join(os.path.dirname(__file__), 'cogs','achievements', 'user_achievements.json')

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
        return {} # 如果不存在，返回空字典
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"錯誤: 解析使用者成就記錄檔案 '{file_path}' 失敗: {e}。將初始化空記錄。")
        return {}
    except Exception as e:
        print(f"載入使用者成就記錄檔案 '{file_path}' 時發生錯誤: {e}。將初始化空記錄。")
        return {}

def save_user_achievements(data, file_path):
    """將使用者成就記錄保存到 JSON 檔案。"""
    try:
        # 確保資料夾存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"使用者成就記錄已保存到 '{file_path}'。")
    except Exception as e:
        print(f"保存使用者成就記錄到 '{file_path}' 時發生錯誤: {e}")


# 載入成就定義和使用者成就記錄
bot.achievements_data = load_achievements(ACHIEVEMENTS_FILE)
bot.user_achievements = load_user_achievements(USER_ACHIEVEMENTS_FILE)
print(f"載入 {len(bot.achievements_data)} 個成就定義。")
print(f"載入 {len(bot.user_achievements)} 個使用者成就記錄。")
# --- 【新增結束】 ---


@bot.event
# 當機器人完成啟動
async def on_ready():   
    print(f"目前登入身份 --> {bot.user}")
    print("----- 載入 Cogs -----")
    # 載入 cogs 資料夾中的所有 .py 檔案
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                # 載入 Cog，例如 'cogs.general'、'cogs.mention_responses'
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"成功載入 {filename}")
            except Exception as e:
                print(f"無法載入 {filename}: {e}")
    print("----- Cogs 載入完成 -----")
    try:
        test_guild_id = 884003698110496803 # <--- 替換成你的伺服器 ID
        synced = await bot.tree.sync()
        print(f"同步了 {len(synced)} 個斜線指令。")
    except Exception as e:
        print(f"同步斜線指令時發生錯誤: {e}")
        
    await bot.change_presence(activity=discord.Game(name="嘎嘎醬的日常生活"))  # 設定機器人狀態為遊戲
    await bot.change_presence(status=discord.Status.online)  # 設定機器人狀態為在線
    log_channel_id = 1384915793783029792  # <-- 替換為你的頻道 ID
    log_channel = bot.get_channel(log_channel_id)
    #if log_channel:
        #await log_channel.send(f"<@1382919972707369051> 姊姊早安，我是嘎嘎嘎!")

# (可選) 載入 Cog 的指令，方便開發時測試和管理
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
bot.run(TOKEN)