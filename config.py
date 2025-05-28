import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 從 .env 中讀取設定
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID"))
APP_ID = int(os.getenv("APP_ID"))
Groq_API_KEY= os.getenv("Groq_API_KEY")