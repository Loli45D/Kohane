import discord
from discord.ext import commands
from discord import app_commands
from config import OWNER_ID, Groq_API_KEY
import aiohttp
import json
import os
import random

# 設定路徑與檔案
MEMORY_PATH = "data/Kohane_Memories"
if not os.path.exists(MEMORY_PATH):
    os.makedirs(MEMORY_PATH)


class KohaneResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.groq_api_key = Groq_API_KEY
        self.system_promot = (
            "[System promot] 請依照以下格式輸入訊息：\n"
            "[System promot]\n[kohane memory]（僅限主人）\n[性格設定]\n[回朔訊息]（可能沒有）\n[主要內容]\n\n"
            "僅限主人的訊息才會讀寫記憶，回朔訊息僅在必要時使用以避免冗餘。小花音輸出格式為：\n"
            "［本文］\n［記憶］（僅限主人）"
        )
        self.model_data = {
            "model": "mixtral-8x7b-32768",
            "url": "https://api.groq.com/openai/v1/chat/completions"
        }
        self.owner_id = OWNER_ID
        self.guest_id = []
        self.ban_id = []
        self.max_token = 2048
        self.master_promot = "愛主人的小花音~"
        self.guest_promot = "禮貌接待的女僕小花音"
        self.stranger_promot = "冷冷的小花音...沒興趣搭理你呢～"

    async def fetch_reply(self, payload):
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.model_data["url"], headers=headers, data=json.dumps(payload)) as resp:
                if resp.status != 200:
                    return f"(｡•́︿•̀｡) 小花音出錯了喵～錯誤碼 {resp.status}"
                try:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                except Exception as e:
                    print(f"API 回應解析錯誤: {e}")
                    return "圖片或回應解析錯誤了喵～可能主人設定太大或格式有誤(；ω；)"

    async def fetch_history(self, ctx, max_token):
        """
        根據token限制，往上撈訊息直到token上限
        """
        history = []
        token_count = 0
        async for msg in ctx.channel.history(limit=30, oldest_first=False):
            if msg.author.bot or msg.id == ctx.id:
                continue
            content = msg.content.strip()
            if not content:
                continue
            tokens = self.count_token(content)
            if token_count + tokens > max_token:
                break
            history.insert(0, content)
            token_count += tokens
        return "\n".join(history)

    def count_token(self, text):
        # 只計算字數
        return len(text)

    def build_prompt(self, user_id, memory, personality, history, content):
        # personality 根據身份自動選擇
        if user_id == self.owner_id:
            personality = self.master_promot
        elif user_id in self.guest_id:
            personality = self.guest_promot
        else:
            personality = self.stranger_promot

        system_promot = self.build_system_promot(
            is_owner=user_id == self.owner_id,
            memory=memory if user_id == self.owner_id else None,
            personality=personality,
            history=history,
        )
        messages = []
        if system_promot.strip():
            messages.append({"role": "system", "content": system_promot.strip()})
        if content and content.strip():
            messages.append({"role": "user", "content": f"[主要內容] {content.strip()}"})
        return messages

    def build_system_promot(self, is_owner=False, memory=None, personality=None, history=None):
        lines = ["[System promot] 請依照以下格式輸入訊息："]
        if memory:
            lines.append(f"記憶: {memory}")
        if personality:
            lines.append(f"性格: {personality}")
        if history:
            lines.append(f"回朔訊息: {history}")
        if is_owner:
            lines.append(
                "\n請以 [本文] 回覆主要內容，[記憶] 回覆最新記憶"
            )
        else:
            lines.append(
                "\n[回朔訊息]僅為輔助，請以主要對話為主"
            )
        return "\n".join(lines)

    def load_memory(self, user_id):
        path = os.path.join(MEMORY_PATH, f"{user_id}.txt")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def save_memory(self, user_id, memory):
        path = os.path.join(MEMORY_PATH, f"{user_id}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(memory)

    def get_cold_reply(self):
        try:
            with open(os.path.join("data", "cold_replies.json"), "r", encoding="utf-8") as f:
                replies = json.load(f)
                return random.choice(replies.get("replies", ["（冷冷地看了你一眼，沒說話）"]))
        except:
            return "（小花音冷冷地瞪了你一眼）"

    async def process_message(self, ctx, content):
        user_id = ctx.author.id

        if user_id in self.ban_id:
            await ctx.reply(self.get_cold_reply())
            return

        memory = self.load_memory(user_id) if user_id == self.owner_id else ""
        # 取得回朔訊息
        history = await self.fetch_history(ctx, self.max_token // 2)  # 預留一半token給prompt
        prompt = self.build_prompt(user_id, memory, None, history, content)
        payload = {
            "model": self.model_data["model"],
            "messages": prompt,
            "max_tokens": self.max_token
        }
        reply = await self.fetch_reply(payload)

        if user_id == self.owner_id:
            parts = reply.split("[記憶]")
            main_reply = parts[0].strip()
            new_memory = parts[1].strip() if len(parts) > 1 else memory
            self.save_memory(user_id, new_memory)
        else:
            main_reply = reply.strip()

        await ctx.reply(main_reply)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if self.bot.user in message.mentions:
            content = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            await self.process_message(message, content)

    @app_commands.command(name="ask", description="詢問小花音♡")
    async def ask_kohane(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        await self.process_message(interaction, text)

    @app_commands.command(name="set_model", description="設定模型")
    @app_commands.describe(model="模型名稱", url="API網址")
    async def set_model(self, interaction: discord.Interaction, model: str, url: str):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("只有主人可以設定模型喵～", ephemeral=True)
            return
        self.model_data["model"] = model
        self.model_data["url"] = url
        await interaction.response.send_message(f"模型設定完成喵～\nModel: {model}\nURL: {url}")

    @app_commands.command(name="set_token", description="設定最大Token")
    async def set_token(self, interaction: discord.Interaction, token: int):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("你不是主人喵～不准偷改設定ฅ(=｀ω´=ฅ)", ephemeral=True)
            return
        self.max_token = token
        await interaction.response.send_message(f"最大Token設定為 {token} 喵！")

    @app_commands.command(name="set_guest", description="設定來賓ID")
    async def set_guest(self, interaction: discord.Interaction, id: int):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("你不是主人喵～不准亂動來賓設定ฅ(≖‿≖ฅ)", ephemeral=True)
            return
        if id in self.guest_id:
            await interaction.response.send_message(f"來賓 ID：{id} 已存在", ephemeral=True)
            return
        self.guest_id.append(id)
        await interaction.response.send_message(f"已新增來賓 ID：{id}")

    @app_commands.command(name="set_ban", description="封鎖ID")
    async def set_ban(self, interaction: discord.Interaction, id: int):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("你不是主人喵～不准亂封人！(╬ Ò﹏Ó)", ephemeral=True)
            return
        if id in self.ban_id:
            await interaction.response.send_message(f"ID：{id} 已在封鎖名單", ephemeral=True)
            return
        self.ban_id.append(id)
        await interaction.response.send_message(f"已封鎖 ID：{id}")


async def setup(bot):
    await bot.add_cog(KohaneResponder(bot))
