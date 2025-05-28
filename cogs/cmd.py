# cogs/main.py
import discord
from discord.ext import commands
from discord import app_commands
from bs4 import BeautifulSoup
import requests
from config import OWNER_ID
from core.classes import Cog_Extension


class Main(Cog_Extension):

    # Slash 指令：延遲測試
    @app_commands.command(name="ping", description="顯示延遲")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)

        if interaction.user.id == OWNER_ID:
            # 主人專屬可愛版
            hearts = "💓" * min(latency // 50, 10)
            status = "超快喵～！(≧◡≦)" if latency < 100 else "小花音喘喘的呢... (>﹏<)"

            embed = discord.Embed(
                title="小花音的心跳測量♡",
                description=f"喵嗚～主人目前延遲是 `{latency}ms` 呢～\n{status}\n{hearts}",
                color=discord.Color.pink()
            )
            embed.set_footer(text="只屬於主人的回覆喵♡")
        else:
            # 一般使用者簡版
            embed = discord.Embed(
                title="Pong!",
                description=f"延遲為 `{latency}ms`。",
                color=discord.Color.blurple()
            )

        await interaction.response.send_message(embed=embed)
    # Slash 指令：nhentai
    @app_commands.command(name="nhentai", description="快速取得 nhentai 圖庫網址")
    @app_commands.describe(code="作品代碼")
    async def nhentai(self, interaction: discord.Interaction, code: str):
        await interaction.response.send_message(f"https://nhentai.net/g/{code}/")

    # Slash 指令：Pixiv
    @app_commands.command(name="pixiv", description="快速取得 Pixiv 圖片網址")
    @app_commands.describe(art_id="作品 ID")
    async def pixiv(self, interaction: discord.Interaction, art_id: str):
        await interaction.response.send_message(f"https://www.pixiv.net/artworks/{art_id}/")

    # Slash 指令：DLsite
    @app_commands.command(name="dlsite", description="顯示 DLsite 商品資訊")
    @app_commands.describe(product_id="商品代碼 (如 RJ123456)")
    async def dlsite(self, interaction: discord.Interaction, product_id: str):
        await interaction.response.defer()

        web = f'https://www.dlsite.com/maniax/work/=/product_id/{product_id}.html'
        try:
            res = requests.get(web, timeout=10)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, "html.parser")
            title_elem = soup.select_one("h1")
            image_elem = soup.find(itemprop="image")

            title = title_elem.text.strip() if title_elem else "未找到標題"
            image_url = "https:" + image_elem["src"] if image_elem and "src" in image_elem.attrs else None

            embed = discord.Embed(title=title, url=web, color=discord.Color.blue())
            embed.set_author(
                name="DLsite",
                icon_url="https://www.dlsite.com/images/web/common/logo/pc/logo-dlsite-r18.png"
            )
            if image_url:
                embed.set_image(url=image_url)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"❌ 錯誤：無法抓取商品頁面\n```{e}```")


async def setup(bot):
    await bot.add_cog(Main(bot))
