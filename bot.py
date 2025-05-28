import discord
from discord.ext import commands
import os
import asyncio
import config  # 匯入你的設定檔！

intents = discord.Intents.default()
intents.message_content = True  # 若需要讀取訊息內容（非必要可不打開）

# 🐾 建立 bot 實例（無 command_prefix 因為是用 slash）
bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=config.APP_ID  # 在這裡加入你的機器人 ID
)

@bot.event
async def on_ready():
    print(f"小花音上線囉～帳號：{bot.user}♡")
    try:
        synced = await bot.tree.sync()
        print(f"已同步 {len(synced)} 個 slash 指令ฅ^•ﻌ•^ฅ")
    except Exception as e:
        print("同步失敗喵！", e)

# 🧩 自動載入所有 cogs
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"載入模組：{filename}")
            except Exception as e:
                print(f"載入失敗：{filename}", e)

# 🚀 啟動 bot 主流程
async def main():
    await load_cogs()
    await bot.start(config.TOKEN)

# 🧠 執行
asyncio.run(main())
