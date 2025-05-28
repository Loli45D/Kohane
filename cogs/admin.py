import discord
from discord import app_commands
from discord.ext import commands
from core.classes import Cog_Extension
from config import OWNER_ID, TEST_GUILD_ID  # 將 guild ID 移到設定檔


class Admin(Cog_Extension):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.bot = bot
        self.ready = False  # 新增狀態追蹤

    async def cog_load(self):
        if not self.ready:  # 確保只執行一次
            self.bot.add_listener(self.on_ready)
            self.ready = True

    async def on_ready(self):
        # 在機器人準備好後同步指令
        try:
            if TEST_GUILD_ID:
                guild = discord.Object(id=TEST_GUILD_ID)
                self.bot.tree.copy_global_to(guild=guild)
                await self.bot.tree.sync(guild=guild)
                print(f"已同步指令到測試伺服器 (ID: {TEST_GUILD_ID})")
            else:
                await self.bot.tree.sync()
                print("已同步全域指令")
        except Exception as e:
            print(f"同步指令時發生錯誤: {e}")

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.id == OWNER_ID

    # 修改權限檢查裝飾器
    def is_owner():
        async def predicate(interaction: discord.Interaction):
            if interaction.user.id != OWNER_ID:
                await interaction.response.send_message("這個指令只有主人可以使用喔...", ephemeral=True)
                return False
            return True
        return app_commands.check(predicate)

    # Slash 指令 - 重新載入
    @app_commands.command(name="reload", description="重新載入指定 cog")
    @is_owner()  # 加入權限檢查
    async def reload(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.reload_extension(f"cogs.{extension}")
            await interaction.response.send_message(f"已重新載入 `{extension}` ♡")
        except commands.ExtensionNotFound:
            await interaction.response.send_message(f"找不到模組 `{extension}` 喵...", ephemeral=True)
        except commands.ExtensionNotLoaded:
            await interaction.response.send_message(f"模組 `{extension}` 尚未載入喵...", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"載入失敗喵：```{str(e)}```", ephemeral=True)

    @app_commands.command(name="load", description="載入指定 cog")
    @is_owner()  # 加入權限檢查
    async def load(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.load_extension(f"cogs.{extension}")
            await interaction.response.send_message(f"已載入 `{extension}` ♡")
        except commands.ExtensionAlreadyLoaded:
            await interaction.response.send_message(f"模組 `{extension}` 已經載入了喵...", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"載入失敗喵：```{str(e)}```", ephemeral=True)

    @app_commands.command(name="unload", description="卸載指定 cog")
    @is_owner()  # 加入權限檢查
    async def unload(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.unload_extension(f"cogs.{extension}")
            await interaction.response.send_message(f"已卸載 `{extension}` ♡")
        except commands.ExtensionNotLoaded:
            await interaction.response.send_message(f"模組 `{extension}` 尚未載入喵...", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"卸載失敗喵：```{str(e)}```", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Admin(bot))
