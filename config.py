import os
from tokens import BOT_TOKEN, TELEGRAM_USERS, CHATGPT_TOKEN

# Telegram
AUTHORISED_NAMES = TELEGRAM_USERS.values()
AUTHORISED_IDS = TELEGRAM_USERS.keys()
BOT_TOKEN = BOT_TOKEN

# File Storage
CUSTOM_STORAGE_DIR = os.path.expanduser("~/printbotv2/files")
PICKGUARD_STORAGE_DIR = os.path.expanduser("~/printbot2")
os.makedirs(CUSTOM_STORAGE_DIR, exist_ok=True)

# OpenAI
CHATGPT_TOKEN = CHATGPT_TOKEN

# Sheets
SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/spreadsheets"
]