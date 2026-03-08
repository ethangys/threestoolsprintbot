from telegram import BotCommand

async def register_commands(app):
    
    commands = [
        BotCommand("start", "Show welcome message"),
        BotCommand("newjob", "Add new print job"),
        BotCommand("queue", "Show current queue"),
        BotCommand("remove", "Delete job by ID")
    ]
    await app.bot.set_my_commands(commands)