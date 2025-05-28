# cogs/telegraph_downloader.py
import os
import re
import aiofiles
import asyncio
import typing
import functools
import httpx
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import time
import random

import discord
from discord import app_commands
from discord.ext import commands

from core.classes import Cog_Extension

# 檔案儲存位置
TG_DOWN_FOLDER = "data/ExLoli_Talegraph"

# 建立執行緒池
executor = ThreadPoolExecutor(max_workers=5)


def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, functools.partial(func, *args, **kwargs))
    return wrapper


class TelegraphDownloader(Cog_Extension):

    @app_commands.command(name="tgdownload", description="下載 telegra.ph 圖片")
    @app_commands.describe(urls="請輸入網址（可多個，用空白分隔）")
    async def tg_download(self, interaction: discord.Interaction, urls: str):
        await interaction.response.defer()
        input_list = urls.split()
        results = await self._main(input_list)

        # 發送總結 Embed
        embed = self.build_embed(results)
        await interaction.followup.send(embed=embed)

        # 為每個成功案例發送詳細 Embed
        for result in results:
            if result["success"]:
                detailed_embed = discord.Embed(
                    title=result["name"],
                    url=urls,  # 原始連結
                    colour=0x00b0f4
                )
                detailed_embed.set_author(name="下載完成")
                if result["first_image"]:
                    detailed_embed.set_image(url=result["first_image"])
                await interaction.followup.send(embed=detailed_embed)

    def build_embed(self, results: list[dict]) -> discord.Embed:
        embed = discord.Embed(
            title="Telegraph 圖片下載結果 ✨",
            color=discord.Color.blue()
        )
        for result in results:
            status = "✅ 已完成" if result["success"] else "❌ 失敗"
            name = result["name"]
            link = result.get("first_image")
            field_value = f"[點我看圖片]({link})" if link else "無法取得圖片"
            embed.add_field(name=f"{status}｜{name}", value=field_value, inline=False)
        return embed


    @to_thread
    def _main(self, urls: list[str]):
        os.makedirs(TG_DOWN_FOLDER, exist_ok=True)
        response = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

        def sanitize_filename(name):
            return re.sub(r'[\\/:*?\"<>|]', '', name)

        def download_image(url, path, retries=3, delay=5):
            for attempt in range(retries):
                try:
                    with httpx.stream("GET", url, headers=headers, timeout=15, follow_redirects=True) as r:
                        r.raise_for_status()
                        with open(path, 'wb') as f:
                            for chunk in r.iter_bytes():
                                f.write(chunk)
                    return
                except Exception as e:
                    if attempt < retries - 1:
                        print(f"[警告] 下載失敗，重試中... ({attempt + 1}/{retries})")
                        time.sleep(delay)
                    else:
                        print(f"[錯誤] 無法下載圖片：{url}，錯誤：{e}")
                        raise

        def fetch_page(url, retries=3):
            for i in range(retries):
                try:
                    res = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
                    res.raise_for_status()
                    return res.text
                except httpx.RemoteProtocolError:
                    print(f"[警告] 遠端關閉連線，嘗試第 {i+1} 次")
                    time.sleep(3)
                except Exception as e:
                    raise e
            raise Exception("多次嘗試仍無法取得頁面")

        def create_nomadia_file(path):
            with open(os.path.join(path, '.nomadia'), 'w') as f:
                pass

        for web in urls:
            try:
                html = fetch_page(web)
                soup = BeautifulSoup(html, "html.parser")

                title = soup.select_one('h1')
                Name = sanitize_filename(title.text.strip()) if title else "Untitled"

                img = soup.select('img')
                image_links = [result.get("src") for result in img if result.get("src")]

                folder = os.path.join(TG_DOWN_FOLDER, Name)
                ch_folder = os.path.join(folder, "chapter")
                os.makedirs(ch_folder, exist_ok=True)

                first_image = None
                for index, link in enumerate(image_links):
                    img_url = "https://telegra.ph" + link if link.startswith("/") else link
                    path = os.path.join(ch_folder, f"{index + 1}.jpg")
                    
                    # 儲存第一張圖片的URL
                    if index == 0:
                        first_image = img_url
                        
                    download_image(img_url, path)
                    time.sleep(random.uniform(1.5, 3.0))



                create_nomadia_file(folder)
                # 成功案例
                response.append({
                    "success": True,
                    "name": Name,
                    "first_image": first_image
                })

            except Exception as e:
                with open(os.path.join(TG_DOWN_FOLDER, "TGD_error.md"), 'a', encoding="utf-8") as errfile:
                    errfile.write(web + "\n")
                    response.append({
                        "success": False,
                        "name": "未知標題",
                        "first_image": None
                        })
                print(f"[錯誤] {web}：{e}")

        return response


async def setup(bot):
    await bot.add_cog(TelegraphDownloader(bot))
