import discord
from discord.ext import commands
from core.classes import Cog_Extension
from bs4 import BeautifulSoup
import requests
import time
import asyncio
import platform
import subprocess
from config import OWNER_ID


class CW_Event(Cog_Extension):

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, id=956737049745063996)
        if role:
            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # 特別的 ping 回覆只有主人能收到喔
        if message.content.lower() == 'ping':
            if message.author.id == OWNER_ID:
                await message.channel.send("喵嗚～主人的連線狀態看起來很棒棒呢♡ (`･ω･´)ゞ")
            else:
                await message.channel.send("pong")

        # 這裡可以加你以前的其他訊息事件...

        # 例如ASMR更新（假設頻道ID）
        if message.channel.id == 996312188115492926:
            RJin = message.content
            await self.ASMRinput(RJin)

        # 動畫更新
        if message.channel.id == 996315956458553425:
            ANIsrc = message.content.split()[-1]
            ANIname = message.content.rsplit(ANIsrc, 1)[0]

            channel = self.bot.get_channel(955699979706593310)
            ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

            embed = discord.Embed()
            embed.set_author(name="動畫更新", icon_url="https://cdn.discordapp.com/attachments/957292390975172618/963457289564602368/pngegg.png?size=4096")
            embed.add_field(name=ANIname, value="`╰(*°▽°*)╯`", inline=False)
            embed.set_image(url=ANIsrc)
            embed.set_footer(text=ctime)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == 955699356265218078:
            await self.pingserver("updata", payload.message_id, payload.member)

        if payload.channel_id == 955699764220022825:
            await self.pingserver("plex", payload.message_id, payload.member)

        if payload.message_id == 958601904487804938:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if payload.emoji.name == "plex":
                role = discord.utils.get(guild.roles, id=956737039334793227)
            elif payload.emoji.name == "updata":
                role = discord.utils.get(guild.roles, id=956737045492015174)
            else:
                return
            if member and role:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == 958601904487804938:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            if payload.emoji.name == "plex":
                role = discord.utils.get(guild.roles, id=956737039334793227)
            elif payload.emoji.name == "updata":
                role = discord.utils.get(guild.roles, id=956737045492015174)
            else:
                return
            if member and role:
                await member.remove_roles(role)

    # PING SERVER 函式
    def myping(self, host):
        parameter = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', parameter, '1', host]
        response = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return response == 0

    async def ASMRinput(self, RJin):
        RJin = RJin.split()
        for RJnamber in RJin:
            web = f'https://www.dlsite.com/maniax/work/=/product_id/{RJnamber}.html'
            res = requests.get(web)
            soup = BeautifulSoup(res.text, "html.parser")

            title = soup.select_one("h1")
            titxt = title.text if title else "無標題"

            img = soup.find(itemprop="image")
            src = "https:" + str(img).split('"')[7] if img else None

            channel = self.bot.get_channel(955700081934348298)
            ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

            embed = discord.Embed()
            embed.set_author(name="ASMR 更新", icon_url="https://cdn.discordapp.com/attachments/957292390975172618/963457289564602368/pngegg.png?size=4096")
            embed.add_field(name=titxt, value=web, inline=False)
            if src:
                embed.set_image(url=src)
            embed.set_footer(text=ctime)
            await channel.send(embed=embed)
            await asyncio.sleep(2)

    async def pingserver(self, mode, message_id, member):
        if mode == "plex":
            pingsrc = "192.168.2.212"
            channel_id = 955699764220022825
            title = "PLEX服務"
            tiurl = "https://app.plex.tv"
            tiiconurl = "https://cdn.discordapp.com/attachments/957292390975172618/963457289564602368/pngegg.png"

            ping = self.myping(pingsrc)
            if ping:
                rping = ":green_circle: 正常"
                rcolor = 0xe5a00d
            else:
                rping = ":red_circle: 不正常"
                rcolor = 0xff0000

        elif mode == "updata":
            pinglink = "cwrabbit.com"
            pingcore = "192.168.2.238"
            channel_id = 955699356265218078
            title = "UP Data 服務"
            tiurl = "https://cwrabbit.com"
            tiiconurl = "https://cdn.discordapp.com/attachments/957292390975172618/963460034434576435/preview.png"

            lping = self.myping(pinglink)
            cping = self.myping(pingcore)
            if lping and cping:
                rping = ":green_circle: 正常"
                rcolor = 0x32a0ff
            elif not lping:
                rping = ":red_circle: 域名不正常"
                rcolor = 0xff0000
            elif not cping:
                rping = ":red_circle: 內核不正常"
                rcolor = 0xff0000
            else:
                rping = ":red_circle: 不正常"
                rcolor = 0xff0000

        channel = self.bot.get_channel(channel_id)
        ctime = time.strftime('%Y-%m-%d %H:%M', time.localtime())

        embed = discord.Embed(title="運行狀態", description=rping, color=rcolor)
        embed.set_author(name=title, url=tiurl, icon_url=tiiconurl)
        embed.add_field(name="檢查時間", value=ctime, inline=True)
        embed.add_field(name="新增任意表情符號更新狀態", value=f"更新者: {member}", inline=False)
        embed.set_footer(text="cwrabbit.com")
        await channel.send(embed=embed)

        if message_id != 0:
            try:
                message = await channel.fetch_message(message_id)
                await message.clear_reactions()
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(CW_Event(bot))
