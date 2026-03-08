from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from db import get_queue_data, insert_job, remove_job, update_status, get_job, update_assigned
from commands.utils import send_all
from config import AUTHORISED_NAMES, AUTHORISED_IDS, CUSTOM_STORAGE_DIR, TELEGRAM_USERS
import os


async def start(update, context):
    keyboard = [["/newjob", "/queue", "/remove"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome! Choose a command below or type a command manually:", reply_markup=reply_markup)

def build_queue_message():
    all_jobs = get_queue_data().items()

    if all(len(jobs) == 0 for _, jobs in all_jobs):
        return "📭 No pending jobs.", None

    buttons = []
    text = "📋 Print Queue:\n\n"
    i = 1

    for status_name, jobs in all_jobs:

        if status_name == "Received":
            header = "📥 Received\n"
        elif status_name == "Printing":
            header = "🖨️ Printing\n"
        else:
            header = "✅ Printed\n"

        text += header

        for job in jobs:
            id, customer_name, file_name, assigned_user, status, position = job

            text += f"{i}. {customer_name} - {file_name} [{assigned_user}]: {status} (ID: {id})\n"

            buttons.append([
                InlineKeyboardButton(f"📂 Get #{i}", callback_data=f"get_{id}"),
                InlineKeyboardButton(f"🟢 Status #{i}", callback_data=f"status_{i}_{customer_name}_{file_name}_{assigned_user}_{status}_{id}")
            ])

            i += 1

        text += "\n"

    reply_markup = InlineKeyboardMarkup(buttons)

    return text, reply_markup

async def queue(update, context):
    text, reply_markup = build_queue_message()
    await update.message.reply_text(text, reply_markup=reply_markup)
    
async def send_queue(context):
    text, reply_markup = build_queue_message()
    
    for user_id in AUTHORISED_IDS:
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)

async def newjob(update, context):
    
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /newjob <position> <assigned_user> <file_name>")
        return
    
    # Ensure pos is int
    try:
        pos = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Position must be a number.")
        return
    
    # Ensure assigned user exists
    if context.args[1].upper() not in AUTHORISED_NAMES:
        await update.message.reply_text("❌ Assigned user not in database")
        return
    else:
        assigned_user = context.args[1].lower().capitalize()
        
    # Set remaining args to file name
    file_name = " ".join(context.args[2:])
    
    # Set bot context variables for file handling
    context.user_data["position"] = pos
    context.user_data["file_name"] = file_name
    context.user_data["assigned_user"] = assigned_user
    
    # Prompt user to upload file/link
    await update.message.reply_text(
        f"📎 Send me the file for '{file_name}'\n"
        f"👤 Assigned to: {assigned_user}\n"
        f"📍 Position: {pos}")

async def handle_file(update, context):
    # Check that user has successfully send /newjob
    if "assigned_user" not in context.user_data or "file_name" not in context.user_data or "position" not in context.user_data:
        await update.message.reply_text("⚠️ Please use /newjob <position> <assigned_to> <name> first before sending a file")
        return
    pos = context.user_data["position"]
    file_name = context.user_data["file_name"]
    assigned_user = context.user_data["assigned_user"]
    
    file = await update.message.document.get_file() # Get file object
    local_path = os.path.join(CUSTOM_STORAGE_DIR, update.message.document.file_name) # Create path using file name
    await file.download_to_drive(local_path) # Download to pi
    
    insert_job(file_name, assigned_user, pos, local_path)
    
    await update.message.reply_text(f"✅ Added Job {file_name} at position {pos}.")
    
    del context.user_data["position"]
    del context.user_data["file_name"]
    del context.user_data["assigned_user"]

    await send_queue(update, context)
    
async def remove(update, context):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /remove <ID>")
        return
    
    try:
        job_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID must be a number.")
    
    job_path = get_job(job_id)[2]
    
    if os.path.dirname(job_path) == CUSTOM_STORAGE_DIR:
        if job_path and os.path.exists(job_path):
            try:
                os.remove(job_path)
            except Exception as e:
                print(f"⚠️ Could not delete file {job_path}: {e}")
    
    remove_job(job_id)
    
    await send_all(context, f"❌ Job ID {job_id} has been cancelled")

async def button_callback(update, context):
    
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("get_"):
        job_id = int(data.split("_")[1])
        job_path = get_job(job_id)[2]
        if job_path and os.path.exists(job_path):
            await context.bot.send_document(chat_id=query.from_user.id, document=open(job_path, "rb"))
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text="❌ File not found.")
    
    elif data.startswith("status_"):
        _, pos, customer_name, file_name, assigned_user, status, job_id = data.split("_")
        
        status_buttons = [
            [
                InlineKeyboardButton("🖨 Printing", callback_data=f"printing_{job_id}_{pos}_{customer_name}"),
                InlineKeyboardButton("✅ Printed", callback_data=f"printed_{job_id}_{pos}_{customer_name}")
            ],
            [
                InlineKeyboardButton("📦 Dispatched", callback_data=f"dispatched_{job_id}"),
                InlineKeyboardButton("🖐️ Claim", callback_data=f"claim_{job_id}")
            ]
        ]
        
        # New inline buttons for individual statuses
        keyboard = InlineKeyboardMarkup(status_buttons)
        
        # Send new message for modifying status
        await query.message.reply_text(f"Job #{pos}. {customer_name} - {file_name} [{assigned_user}]: {status} (ID: {job_id})", reply_markup=keyboard)
        await query.answer()
    
    elif data.startswith(("printing_", "printed_")):
        status, job_id, pos, customer_name = data.split("_")
        update_status(job_id, status)
        
        send_all(f"Job #{pos} status set to {status.capitalize()} ✅")
        
        await send_queue(context)
        
    elif data.startswith("dispatched_"):
        job_id = data.split("_")[1]
        job_path = get_job(job_id)[2]
        if os.path.dirname(job_path) == CUSTOM_STORAGE_DIR:
            if job_path and os.path.exists(job_path):
                try:
                    os.remove(job_path)
                except Exception as e:
                    print(f"⚠️ Could not delete file {job_path}: {e}")
        
        remove_job(job_id)
        
        await send_queue(context)
    
    else:
        job_id = data.split("_")[1]
        assigned_user = TELEGRAM_USERS.get(update.callback_query.from_user.id)
        await query.message.reply_text(f"You have claimed job with ID: {job_id}")
        await query.answer()
        update_assigned(job_id, assigned_user.capitalize())
        await send_queue(context)