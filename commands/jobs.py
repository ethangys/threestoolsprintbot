from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from db import get_queue_data, insert_job, remove_job, update_status, get_job, update_assigned, update_file_path, check_existing_file_path
from commands.utils import send_all, delete_file
from config import AUTHORISED_NAMES, AUTHORISED_IDS, CUSTOM_STORAGE_DIR, TELEGRAM_USERS
import os
import shlex


async def start(update, context):
    keyboard = [["/newjob", "/queue"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome! Choose a command below or type a command manually:", reply_markup=reply_markup)

def build_queue_message(context):
    all_jobs = get_queue_data().items()
    
    user = context.user_data.get("user", "").capitalize()
    
    has_jobs = False
    
    buttons = []
    text = "📋 Print Queue:\n\n"
    i = 1

    for status_name, jobs in all_jobs:
        
        if user:
            jobs = [job for job in jobs if job[3] == user]
        if not jobs:
            continue
        has_jobs = True

        if status_name == "Received":
            text += "📥 Received\n"
        elif status_name == "Printing":
            text += "🖨️ Printing\n"
        else:
            text += "✅ Printed\n"

        for job in jobs:
            id, customer_name, file_name, assigned_user, status, position, file_path, errors = job
             
            text += f"{i}. {customer_name} - {file_name} [{assigned_user}]: {status}\n"

            buttons.append([
                InlineKeyboardButton(f"📂 #{i}", callback_data=f"get_{id}_{i}"),
                InlineKeyboardButton(f"📊 #{i}", callback_data=f"status_{id}_{i}"),
                InlineKeyboardButton(f"❌ #{i}", callback_data = f"remove_{id}_{i}")
            ])
            i += 1

        text += "\n"
    if not has_jobs:
        return "📭 No pending jobs.", None


    reply_markup = InlineKeyboardMarkup(buttons)

    return text, reply_markup

async def queue(update, context):
    if len(context.args) == 1:
        if context.args[0].upper() in (list(AUTHORISED_NAMES) + ["MANUAL"]):
            context.user_data["user"] = context.args[0]
        else:
            await update.message.reply_text("User not authorised")
    text, reply_markup = build_queue_message(context)
    if len(context.args) == 1:
        del context.user_data["user"]
    await update.message.reply_text(text, reply_markup=reply_markup)
    
async def send_queue(context):
    text, reply_markup = build_queue_message(context)
    
    for user_id in AUTHORISED_IDS:
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)

async def newjob(update, context):
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /newjob <position> <assigned_user> '<customer_name>' <file_name>\nTo add to end of queue, set position to 0")
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
    
    # Extract customer name and file name from remaining args
    args_str = " ".join(context.args[2:])
    # Split args by by ''
    parsed_args = shlex.split(args_str)
    # Extract customer name and file name
    customer_name = parsed_args[0]
    file_name = " ".join(parsed_args[1:])
    
    if customer_name == '':
        customer_name = "Manual"
    # Set bot context variables for file handling
    context.user_data["position"] = pos
    context.user_data["customer_name"] = customer_name
    context.user_data["file_name"] = file_name
    context.user_data["assigned_user"] = assigned_user
    
    # Prompt user to upload file/link
    await update.message.reply_text(
        f"📎 Send me the file for '{file_name}'\n"
        f"👤 Assigned to: {assigned_user}\n"
        f"📍 Position: {pos}")

async def handle_file(update, context):
    # Check that user has successfully send /newjob or pressed upload button from queue
    if ("assigned_user" not in context.user_data or "file_name" not in context.user_data or "position" not in context.user_data) and "file_path" not in context.user_data:
        await update.message.reply_text("⚠️ Please use /newjob <position> <assigned_to> <name> first before sending a file or trigger through upload button in /queue -> 📊")
        return
    
    document = update.message.document
    text = update.message.text
    
    # Get file object
    if document:
        file = await document.get_file()
    
    # If job has valid file path (Fetched from etsy)
    if "file_path" in context.user_data:
        # If requires customisation
        if context.user_data["file_path"] == "custom":
            # Upload to custom storage directory to be deleted later
            file_path = os.path.join(CUSTOM_STORAGE_DIR, update.message.document.file_name)
            await file.download_to_drive(file_path)
            update_file_path(file_path, context.user_data["job_id"])
            del context.user_data["job_id"]
        else:
            # Upload to pickguard storage directory to be preserved for future downloads
            file_path = context.user_data["file_path"]
            await file.download_to_drive(file_path)
        del context.user_data["file_path"]
        
    # For manually added jobs
    else:
        customer_name = context.user_data["customer_name"]
        pos = context.user_data["position"]
        file_name = context.user_data["file_name"]
        assigned_user = context.user_data["assigned_user"]
        if document:
            file_path = os.path.join(CUSTOM_STORAGE_DIR, update.message.document.file_name) # Create path using file name
            await file.download_to_drive(file_path) # Download to pi
        elif text:
            file_path = ""
        insert_job(file_name, pos, assigned_user, file_path, customer_name)
        await update.message.reply_text(f"✅ Added Job: {file_name} at {f'position {pos}' if pos != 0 else 'end of queue'}.")
        del context.user_data["position"]
        del context.user_data["file_name"]
        del context.user_data["assigned_user"]
        del context.user_data["customer_name"]


    await send_queue(context)

async def button_callback(update, context):
    
    # Fetch data from pressed button
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # Get button handler
    if data.startswith("get_"):
        job_id = int(data.split("_")[1])
        job_path = get_job(job_id)[2]
        if job_path and os.path.exists(job_path):
            await context.bot.send_document(chat_id=query.from_user.id, document=open(job_path, "rb"))
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text="❌ File not found.")
            
    # Remove button handler
    elif data.startswith("remove_"):
        job_id = int(data.split("_")[1])
        job_pos = int(data.split("_")[2])
        job_path = get_job(job_id)[2]
        if not check_existing_file_path(job_path):
            delete_file(job_path)
        remove_job(job_id)
        
        await send_all(context, f"❌ Job #{job_pos} has been cancelled")
        await send_queue(context)
    
    # Status button handler
    elif data.startswith("status_"):
        job_id = data.split("_")[1]
        job_pos = data.split("_")[2]
        customer_name, file_name, file_path, assigned_user, status, pos, errors = get_job(job_id)
        
        status_buttons = [
            [
                InlineKeyboardButton("🖨 Printing", callback_data=f"printing_{job_id}_{job_pos}"),
                InlineKeyboardButton("✅ Printed", callback_data=f"printed_{job_id}_{job_pos}")
            ],
            [
                InlineKeyboardButton("📦 Dispatched", callback_data=f"dispatched_{job_id}_{job_pos}"),
                InlineKeyboardButton("🖐️ Claim", callback_data=f"claim_{job_id}_{job_pos}")
            ]
        ]
        
        # Upload button if file does not exist
        if not os.path.exists(get_job(job_id)[2]):
            status_buttons.append([InlineKeyboardButton("⬆️ Upload", callback_data=f"upload_{job_id}_{job_pos}")])
        
        # New inline buttons for individual statuses
        keyboard = InlineKeyboardMarkup(status_buttons)
        
        # Send new message for modifying status
        await query.message.reply_text(f"Job #{job_pos}: {customer_name} - {file_name} [{assigned_user}]: {status}", reply_markup=keyboard)
        await query.answer()
    
    # Printing/Printed button handlers
    elif data.startswith(("printing_", "printed_")):
        new_status = data.split("_")[0]
        job_id = data.split("_")[1]
        job_pos = data.split("_")[2]
        customer_name, file_name, file_path, assigned_user, status, position, errors = get_job(job_id)
        update_status(job_id, new_status.capitalize())
        
        await send_all(context, message=f"Job #{job_pos}: {customer_name} - {file_name} [{assigned_user}] status set to {new_status.capitalize()} ✅")
        
        await send_queue(context)
    
    # Dispatch button handler
    elif data.startswith("dispatched_"):
        job_id = data.split("_")[1]
        job_pos = data.split("_")[2]
        customer_name, file_name, file_path, assigned_user, status, position, errors = get_job(job_id)
        # Only delete if it is located in custom directory and not being used by another job
        if not check_existing_file_path(file_path):
            delete_file(file_path)
        
        await send_all(context, message=f"Job #{job_pos}: {customer_name} - {file_name} [{assigned_user}] has been dispatched 📦")
        
        remove_job(job_id)
        
        await send_queue(context)
        
    # Upload button handler
    elif data.startswith("upload_"):
        
        job_id = data.split("_")[1]
        job_pos = data.split("_")[2]
        job = get_job(job_id)
        file_path = job[2]
        errors = job[6]
        
        await query.message.reply_text(f"📎 Send me the file for Job #{job_pos}")
        await query.answer()
        if not errors:
            context.user_data["file_path"] = file_path
        else:
            context.user_data["file_path"] = "custom"
            context.user_data["job_id"] = job_id
        
    else:
        job_id = data.split("_")[1]
        job_pos = data.split("_")[2]
        assigned_user = TELEGRAM_USERS.get(update.callback_query.from_user.id)
        await query.message.reply_text(f"You have claimed Job #{job_pos}")
        await query.answer()
        update_assigned(job_id, assigned_user.capitalize())
        
        await send_queue(context)