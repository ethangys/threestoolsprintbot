from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, AUTHORISED_IDS
from commands.jobs import start, newjob, queue, button_callback, handle_file, prints, jobs, glossy
from commands.utils import block_unauthorised
from commands.setup import register_commands, start_polling


app = Application.builder().token(BOT_TOKEN).post_init(register_commands).post_init(start_polling).build()

user_filter = filters.User(user_id=AUTHORISED_IDS)

app.add_handler(CommandHandler("start", start, filters=user_filter))
app.add_handler(CommandHandler("newjob", newjob, filters=user_filter))
app.add_handler(CommandHandler("queue", queue, filters=user_filter))
app.add_handler(CommandHandler("prints", prints, filters=user_filter))
app.add_handler(CommandHandler("glossy", glossy, filters=user_filter))
app.add_handler(CommandHandler("jobs", jobs, filters=user_filter))
app.add_handler(CallbackQueryHandler(button_callback))
app.add_handler(MessageHandler((filters.Document.ALL | (filters.TEXT & ~filters.COMMAND)) & user_filter, handle_file))
app.add_handler(MessageHandler(filters.ALL, block_unauthorised))

app.run_polling() 
