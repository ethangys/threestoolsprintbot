from config import CHATGPT_TOKEN, AUTHORISED_IDS
import asyncio

async def send_all(context, message):
    for user_id in AUTHORISED_IDS:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            print(f"⚠️ Could not send message to {user_id}: {e}")
            
async def block_unauthorised(update, context):
    user_id = update.effective_user.id
    if user_id not in AUTHORISED_IDS:
        await update.message.reply_text("❌ You are not allowed to use this bot.")
        return True