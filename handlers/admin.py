from telegram import Update
from telegram.ext import ContextTypes
import config
import database

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_html("⛔️ Access Denied. Admin privileges required.")
        return

    users, surveys, responses = await database.get_admin_stats()
    
    admin_msg = (
        "⚙️ <b>Admin Dashboard</b>\n\n"
        f"👤 Total Registered Users: <b>{users}</b>\n"
        f"📝 Total Surveys Created: <b>{surveys}</b>\n"
        f"💬 Total Responses Recorded: <b>{responses}</b>\n\n"
        "<b>Commands:</b>\n"
        "<code>/broadcast &lt;message&gt;</code> - Broadcast text message to all users"
    )
    await update.message.reply_html(admin_msg)

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_html("⛔️ Access Denied.")
        return

    if not context.args:
        await update.message.reply_html("⚠️ Usage: <code>/broadcast Your message text here</code>")
        return

    broadcast_text = " ".join(context.args)
    user_ids = await database.get_all_user_ids()
    
    success = 0
    failed = 0
    
    await update.message.reply_html(f"⏳ Starting broadcast to {len(user_ids)} users...")
    
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 <b>Announcement:</b>\n\n{broadcast_text}", parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_html(
        f"✅ <b>Broadcast Completed</b>\n\n"
        f"Sent successfully: {success}\n"
        f"Failed: {failed}"
    )
