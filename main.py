from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, AUTHORISED_IDS
from commands.jobs import start, newjob, queue, button_callback, handle_file
from commands.utils import block_unauthorised
from commands.setup import register_commands
from commands.etsy import format_order
import asyncio

app = Application.builder().token(BOT_TOKEN).build()

user_filter = filters.User(user_id=AUTHORISED_IDS)

format_order()

app.add_handler(CommandHandler("start", start, filters=user_filter))
app.add_handler(CommandHandler("newjob", newjob, filters=user_filter))
app.add_handler(CommandHandler("queue", queue, filters=user_filter))
app.add_handler(CallbackQueryHandler(button_callback))
app.add_handler(MessageHandler((filters.Document.ALL | (filters.TEXT & ~filters.COMMAND)) & user_filter, handle_file))
app.add_handler(MessageHandler(filters.ALL, block_unauthorised))

asyncio.get_event_loop().create_task(register_commands(app))

app.run_polling() 