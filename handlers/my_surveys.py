from telegram import Update
from telegram.ext import ContextTypes
import database
from utils.keyboards import survey_item_keyboard, main_menu_keyboard

async def my_surveys_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    surveys = await database.get_user_surveys(user_id)
    
    query = update.callback_query
    if query:
        await query.answer()

    if not surveys:
        msg = "📊 You haven't created any surveys yet!"
        if query:
            await query.edit_message_text(msg, reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_html(msg, reply_markup=main_menu_keyboard())
        return

    msg = "📊 <b>Your Surveys:</b>\n\nSelect a survey to manage or view results:"
    bot_info = await context.bot.get_me()
    
    for s in surveys:
        status_icon = "🔴 Closed" if s["is_closed"] else "🟢 Active"
        info_text = (
            f"📋 <b>{s['title']}</b>\n"
            f"Status: {status_icon} | Responses: {s['response_count']}\n"
            f"Created: {s['created_at'][:10]}"
        )
        markup = survey_item_keyboard(s["id"], bool(s["is_closed"]), bot_info.username)
        
        if query:
            await query.message.reply_html(info_text, reply_markup=markup)
        else:
            await update.message.reply_html(info_text, reply_markup=markup)

async def survey_management_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("toggle_"):
        survey_id = data.replace("toggle_", "")
        srv = await database.get_survey(survey_id)
        if srv:
            new_closed = not bool(srv["is_closed"])
            await database.toggle_survey_status(survey_id, new_closed)
            status_text = "Closed" if new_closed else "Reopened"
            await query.edit_message_text(f"✅ Survey status updated to: <b>{status_text}</b>", parse_mode="HTML", reply_markup=main_menu_keyboard())
            
    elif data.startswith("delete_"):
        survey_id = data.replace("delete_", "")
        await database.delete_survey(survey_id)
        await query.edit_message_text("🗑 Survey deleted successfully.", reply_markup=main_menu_keyboard())
