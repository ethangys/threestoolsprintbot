from telegram import BotCommand
from commands.shopify_consolidated import get_orders
import asyncio

async def register_commands(app):
    
    commands = [
        BotCommand("start", "Show welcome message"),
        BotCommand("newjob", "Add new print job"),
        BotCommand("queue", "Show current queue"),
        BotCommand("prints", "Show current print jobs"),
        BotCommand("jobs", "Show ready to dispatch jobs")
    ]
    await app.bot.set_my_commands(commands)
    
async def start_polling(app):
    async def orders_loop():
        while True:
            try:
                await get_orders()
            except Exception as e:
                print(f"Error in get_orders: {e}")
                await asyncio.sleep(10)
    asyncio.create_task(orders_loop())