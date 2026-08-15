from telegram import Update
from telegram.ext import ContextTypes
import database
from utils.keyboards import main_menu_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await database.add_user(user.id, user.username or "", user.first_name or "User")
    
    # Check for deep-linking (Taking survey)
    if context.args and context.args[0].startswith("survey_"):
        survey_id = context.args[0].replace("survey_", "")
        from handlers.take_survey import initiate_take_survey
        await initiate_take_survey(update, context, survey_id)
        return

    welcome_text = (
        f"👋 Welcome to <b>Survey Creator Bot</b>, {user.first_name}!\n\n"
        "Easily create interactive surveys, share them across Telegram, and collect response analytics in real-time.\n\n"
        "Choose an option below to get started:"
    )
    
    if update.message:
        await update.message.reply_html(welcome_text, reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(welcome_text, parse_mode="HTML", reply_markup=main_menu_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "<b>📖 Survey Creator Bot Guide</b>\n\n"
        "<b>Commands:</b>\n"
        "/start - Main menu\n"
        "/mysurveys - View & manage your surveys\n"
        "/results - Inspect survey results\n"
        "/cancel - Abort current ongoing conversation\n"
        "/help - Display this user guide\n\n"
        "<b>Creating Surveys:</b>\n"
        "1. Tap 📝 <i>Create Survey</i>\n"
        "2. Add Title, Description & set Anonymity\n"
        "3. Add Single/Multiple Choice, Yes/No, or Short Text questions\n"
        "4. Publish and share your unique link!\n"
    )
    if update.message:
        await update.message.reply_html(help_text, reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(help_text, parse_mode="HTML", reply_markup=main_menu_keyboard())
