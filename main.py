# 導入Discord.py模組
import discord
# 導入commands指令模組
from discord.ext import commands
import os # 導入 os 模組，用於讀取資料夾中的檔案
from dotenv import load_dotenv


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