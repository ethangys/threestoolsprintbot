from config import CHATGPT_TOKEN, AUTHORISED_IDS, CUSTOM_STORAGE_DIR
from db import remove_job
import os
import asyncio
from openai import OpenAI
from order_management import PROMPT

async def send_all(bot, message, reply_markup=None):
    for user_id in AUTHORISED_IDS:
        try:
            await bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup)
        except Exception as e:
            print(f"⚠️ Could not send message to {user_id}: {e}")
            
async def block_unauthorised(update, context):
    user_id = update.effective_user.id
    if user_id not in AUTHORISED_IDS:
        await update.message.reply_text("❌ You are not allowed to use this bot.")
        return True
    
def delete_file(file_path):
    if os.path.dirname(file_path) == CUSTOM_STORAGE_DIR:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Could not delete file {file_path}: {e}")
                
def gpt_request(prompt):
    client = OpenAI(api_key=CHATGPT_TOKEN)
    response = client.responses.create(
        model = "gpt-4o-mini",
        input = [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature = 0
    )
    
    return response.output_text

def chunk_list(data, chunk_size=30):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]