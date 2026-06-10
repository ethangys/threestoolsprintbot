from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Bot
from db import get_queue_data, insert_job, remove_job, update_status, get_job, update_assigned, update_file_path, check_existing_file_path, update_job_name, unflag, update_glossy
from commands.utils import send_all, delete_file, chunk_list
from config import AUTHORISED_NAMES, CUSTOM_STORAGE_DIR, TELEGRAM_USERS, BOT_TOKEN
import os
import shlex
import json
from pathlib import Path


async def start(update, context):
    keyboard = [["/newjob", "/queue"], ["/prints", "/glossy"], ["/jobs"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome! Choose a command below or type a command manually:", reply_markup=reply_markup)

def format_queue(all_jobs):
    messages = []
    i = 1

    if not any(jobs for _, jobs in all_jobs):
        return [("📭 No pending jobs.", None)]

    flattened_jobs = []
    for status_name, jobs in all_jobs:
        for job in jobs:
            flattened_jobs.append((status_name, job))

    for chunk in chunk_list(flattened_jobs):
        text = ""
        buttons = []
        last_status = None
        for status_name, job in chunk:
            id, customer_name, file_name, assigned_user, status, position, file_path, errors, other_requests, glossy, source = job

            # Show status header if new
            if status_name != last_status:
                if status_name == "Received":
                    text += "📥 Received\n\n"
                elif status_name == "Printing":
                    text += "\n🖨️ Printing\n\n"
                elif status_name == "Printed":
                    text += "\n🖌️ Glossy\n\n"
                else:
                    text += "\n✅ Complete\n\n"
                last_status = status_name

            text += f"{i}. {'[FLAG]' if json.loads(errors) else ''} {customer_name} - {file_name} [{assigned_user}]: {status} {'(NO FILE)' if not file_path or not os.path.exists(file_path) else ''}\n"

            buttons.append([
                InlineKeyboardButton(f"📂 #{i}", callback_data=f"get_{id}_{i}"),
                InlineKeyboardButton(f"📊 #{i}", callback_data=f"status_{id}_{i}"),
                InlineKeyboardButton(f"🖐️ #{i}", callback_data=f"claim_{id}_{i}")
            ])
            i += 1
        text += "\n"
        reply_markup = InlineKeyboardMarkup(buttons)
        messages.append((text, reply_markup))

    return messages


def build_queue_message():
    all_jobs = get_queue_data().items()
    return format_queue(all_jobs)

async def queue(update, context):
    messages = format_queue(get_queue_data().items())
    for text, reply_markup in messages:
        await update.message.reply_text(text, reply_markup=reply_markup)
    
def format_prints(assigned_user=None):
    all_jobs = get_queue_data()
    all_jobs.pop("Complete", None)
    all_jobs.pop("Printed", None)
    if assigned_user:
        filtered = {}
        for status, jobs in all_jobs.items():
            filtered_jobs = [job for job in jobs if job[3] == assigned_user]
            if filtered_jobs:
                filtered[status] = filtered_jobs
        all_jobs = filtered

    return format_queue(all_jobs.items())

async def prints(update, context, assigned_user=None):
    
    if len(context.args) > 1:
        await update.message.reply_text("Usage: /prints or /prints <name>")
        return
    
    if len(context.args) == 1:
        if context.args[0].upper() not in AUTHORISED_NAMES:
            await update.message.reply_text("❌ Assigned user not in database")
            return
        else:
            assigned_user = context.args[0].capitalize()
    
    messages = format_prints(assigned_user)
    for text, reply_markup in messages:
        await update.message.reply_text(text, reply_markup=reply_markup)
        
def format_glossy():
    
    all_jobs = get_queue_data().get("Printed", "")
    if not all_jobs:
        return [("📭 No pending jobs.", None)]
    
    messages = []
    i = 1
    for chunk in chunk_list(all_jobs):
        text = "🖌️ To Glossy:\n\n"
        buttons = []
        for job in chunk:
            id, customer_name, file_name, assigned_user, status, position, file_path, errors, other_requests, glossy, source = job
            text += f"{i}. {customer_name} - {file_name} [{assigned_user}]\n"
            buttons.append([
                InlineKeyboardButton(f"✅ #{i}", callback_data=f"complete_{id}_{i}"),
                InlineKeyboardButton(f"📊 #{i}", callback_data=f"status_{id}_{i}"),
                InlineKeyboardButton(f"❌ #{i}", callback_data=f"remove_{id}_{i}")
            ])
            i += 1
        reply_markup = InlineKeyboardMarkup(buttons)
        messages.append((text, reply_markup))
    
    return messages

async def glossy(update, context):
    messages = format_glossy()
    for text, reply_markup in messages:
        await update.message.reply_text(text, reply_markup=reply_markup)

def format_jobs():
    all_jobs = get_queue_data().get("Complete", "")
    if not all_jobs:
        return [("📭 No pending jobs.", None)]
    
    messages = []
    i = 1
    for chunk in chunk_list(all_jobs):
        text = "📦 To Ship:\n\n"
        buttons = []
        for job in chunk:
            id, customer_name, file_name, assigned_user, status, position, file_path, errors, other_requests, glossy, source = job
            text_source = ""
            if source == "Etsy":
                text_source = "🔵 "
            elif source == "Online Store":
                text_source = "🟢 "
            text += f"{i}. {text_source}{customer_name} - {file_name} [{assigned_user}]\n"
            buttons.append([
                InlineKeyboardButton(f"📦 #{i}", callback_data=f"dispatched_{id}_{i}"),
                InlineKeyboardButton(f"📊 #{i}", callback_data=f"status_{id}_{i}"),
                InlineKeyboardButton(f"❌ #{i}", callback_data=f"remove_{id}_{i}"),
            ])
            i += 1
        reply_markup = InlineKeyboardMarkup(buttons)
        messages.append((text, reply_markup))
    
    return messages

async def jobs(update, context):
    messages = format_jobs()
    for text, reply_markup in messages:
        await update.message.reply_text(text, reply_markup=reply_markup)
    
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
    # Handle edit job name
    if context.user_data.get("editing_job") and update.message.text:
        new_name = update.message.text
        job_id = context.user_data["job_id"]
        name_list = new_name.split(" ")
        if any(x == "Glossy" for x in name_list):
            update_glossy(job_id, 1)
        else:
            update_glossy(job_id, 0)
        update_job_name(new_name, job_id)
        
        del context.user_data["editing_job"]
        del context.user_data["job_id"]
        
        await update.message.reply_text(f"✅ Job name updated to: {new_name}")
        return
    
    if context.user_data.get("editing_link") and update.message.text:
        new_path = update.message.text
        job_id = context.user_data["job_id"]
        update_file_path(new_path, job_id)
        
        del context.user_data["editing_link"]
        del context.user_data["job_id"]
        
        await update.message.reply_text(f"✅ Job path updated to: {new_path}")
        return
    
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
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(context.user_data["job_id"])
        # If requires customisation
        if context.user_data["file_path"] == "custom":
            # Upload to custom storage directory to be deleted later
            file_path = os.path.join(CUSTOM_STORAGE_DIR, update.message.document.file_name)
            await file.download_to_drive(file_path)
            update_file_path(file_path, context.user_data["job_id"])
        else:
            # Upload to pickguard storage directory to be preserved for future downloads
            file_path = Path(context.user_data["file_path"])
            file_path.parent.mkdir(parents=True, exist_ok=True)
            await file.download_to_drive(file_path)
        del context.user_data["file_path"]
        del context.user_data["job_id"]
        await send_all(context.bot, f"✅ File uploaded for {customer_name} - {file_name} [{assigned_user}]")
        
        # for message, reply_markup in format_prints():
        #     await update.message.reply_text(message, reply_markup=reply_markup)
        
    # For manually added jobs
    else:
        customer_name = context.user_data["customer_name"]
        pos = context.user_data["position"]
        file_name = context.user_data["file_name"]
        assigned_user = context.user_data["assigned_user"]
        if document:
            file_path = os.path.join(CUSTOM_STORAGE_DIR, update.message.document.file_name)
            await file.download_to_drive(file_path)
        elif text:
            file_path = ""
        insert_job(file_name=file_name, position=pos, assigned_user=assigned_user, file_path=file_path, customer_name=customer_name, glossy=1, source="")
        await send_all(context.bot, f"✅ Added Job: {file_name} at {f'position {pos}' if pos != 0 else 'end of queue'}.")
        del context.user_data["position"]
        del context.user_data["file_name"]
        del context.user_data["assigned_user"]
        del context.user_data["customer_name"]

async def button_callback(update, context):
    
    user_id = update.effective_user.id
    user_name = TELEGRAM_USERS.get(user_id).capitalize()
    
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
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        remove_job(job_id)
        
        if not check_existing_file_path(file_path):
            delete_file(file_path)
            
        await send_all(context.bot, f"❌ {customer_name} - {file_name} has been cancelled")
    
    elif data.startswith("status_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        
        status_buttons = [
            [
                InlineKeyboardButton("🖨 Printing", callback_data=f"printing_{job_id}"),
                InlineKeyboardButton("📄 Printed", callback_data=f"printed_{job_id}_")
            ],
            [
                InlineKeyboardButton("📦 Dispatched", callback_data=f"dispatched_{job_id}"),
                InlineKeyboardButton("❌ Remove", callback_data=f"remove_{job_id}")
            ]    
        ]
        
        if json.loads(errors):
            status_buttons.append([
                InlineKeyboardButton("🏳️ Unflag", callback_data=f"unflag_{job_id}"),
                InlineKeyboardButton("⚠️ View Errors", callback_data=f"errors_{job_id}")
            ])
        
        if other_requests:
            status_buttons.append([
                InlineKeyboardButton("🙏 Requests", callback_data=f"requests_{job_id}")
                ])
        
        # Upload button if file does not exist
        if not os.path.exists(get_job(job_id)[2]):
            status_buttons.append([InlineKeyboardButton("⬆️ Upload", callback_data=f"upload_{job_id}")])
        
        status_buttons.append([
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{job_id}"),
        ])
        
        # New inline buttons for individual statuses
        keyboard = InlineKeyboardMarkup(status_buttons)
        
        # Send new message for modifying status
        await query.message.reply_text(f"{customer_name} - {file_name} [{assigned_user}]: {status}", reply_markup=keyboard)
        await query.answer()
    
    elif data.startswith("edit_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        
        status_buttons = [
            [
                InlineKeyboardButton("📝 Name", callback_data=f"name_{job_id}"),
                InlineKeyboardButton("🔗 Link", callback_data=f"link_{job_id}")
            ]
        ]
        
        keyboard = InlineKeyboardMarkup(status_buttons)
        await query.message.reply_text(f"{file_name}\n{file_path}", reply_markup=keyboard)
        await query.answer()
    
    elif data.startswith("name_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        
        
        context.user_data["editing_job"] = True
        context.user_data["job_id"] = job_id
        
        await query.message.reply_text(f"✏️ Send the new job name for:\n{file_name}")
        
    elif data.startswith("link_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        
        
        context.user_data["editing_link"] = True
        context.user_data["job_id"] = job_id
        
        await query.message.reply_text(f"✏️ Send the new file path:\nCurrent file path: {file_path}\nDefault file path: /home/joobeepi/printbot2/Pickguards/")
    
    elif data.startswith("errors_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        
        errors_list = json.loads(errors)
        message = "⚠️ Errors:\n"
        errors_message = "\n".join(errors_list)
        message += errors_message
        await query.message.reply_text(message)
    
    elif data.startswith("unflag_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        unflag(job_id)
        await query.message.reply_text(f"{customer_name} - {file_name} has been unflagged ✅")
    
    elif data.startswith("requests_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        await query.message.reply_text(f"Additional Requests: {other_requests}")
        
    elif data.startswith("printing_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        update_status(job_id, "Printing")
        
        await send_all(context.bot, message=f"{customer_name} - {file_name} [{assigned_user}] status set to Printing 🖨️")
        
        for text, reply_markup in format_prints(user_name):
            await query.message.reply_text(text, reply_markup=reply_markup)
        
    elif data.startswith("printed_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        if not glossy:
            update_status(job_id, "Complete")
            await send_all(context.bot, message=f"{customer_name} - {file_name} status set to Complete ✅")
        else:
            update_status(job_id, "Printed")
            await send_all(context.bot, message=f"{customer_name} - {file_name} status set to Printed 📄")
        
        for text, reply_markup in format_prints(user_name):
            await query.message.reply_text(text, reply_markup=reply_markup)
            
    elif data.startswith("complete_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        update_status(job_id, "Complete")
        await send_all(context.bot, message=f"{customer_name} - {file_name} status set to Complete ✅")

    
    elif data.startswith("dispatched_"):
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        completed_jobs = get_queue_data().get("Complete", "")
        for job in completed_jobs:
            order_id = job[0]
            order_name = job[1]
            order_path = job[3]
            if customer_name == order_name:
                remove_job(order_id)
            # Only delete if it is located in custom directory and not being used by another job
            if not check_existing_file_path(order_path):
                delete_file(order_path)
        
        await send_all(context.bot, message=f"Orders for {customer_name} have been dispatched 📦")
        
    elif data.startswith("upload_"):
        
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        
        await query.message.reply_text(f"📎 Send me the file for {customer_name} - {file_name}")
        await query.answer()
        if file_path and file_path != "custom":
            context.user_data["file_path"] = file_path
        else:
            context.user_data["file_path"] = "custom"
        context.user_data["job_id"] = job_id
        
    else:
        job_id = data.split("_")[1]
        customer_name, file_name, file_path, assigned_user, status, position, errors, other_requests, glossy, source = get_job(job_id)
        update_assigned(job_id, user_name)
        
        
        await send_all(context.bot, f"{customer_name} - {file_name} has been claimed by {user_name}")
        
        # for message, reply_markup in format_prints():
        #     await query.message.reply_text(message, reply_markup=reply_markup)

async def addjob(customer_name, file_name, file_path, errors, other_requests, status, glossy, source):
    errors_str = json.dumps(errors)
    insert_job(file_name=file_name, position=0, customer_name=customer_name, file_path=file_path, errors=errors_str, other_requests=other_requests, status=status, glossy=glossy, source=source)
    if status == "Received":
        await send_all(Bot(token=BOT_TOKEN), f"New Job Added: {customer_name} - {file_name} ✅")
    else:
        await send_all(Bot(token=BOT_TOKEN), f"New Job Added and marked as printed: {customer_name} - {file_name} ✅")