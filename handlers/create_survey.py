from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)
import database
from utils.helpers import generate_survey_id
from utils.keyboards import (
    skip_keyboard, anonymous_keyboard, question_type_keyboard,
    add_options_keyboard, next_question_keyboard, publish_keyboard, main_menu_keyboard
)

TITLE, DESCRIPTION, ANONYMOUS, Q_TEXT, Q_TYPE, OPTION_TEXT, NEXT_ACTION, CONFIRM_PUBLISH = range(8)

async def start_create_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    context.user_data["survey"] = {
        "title": "",
        "description": "",
        "is_anonymous": False,
        "questions": [],
        "current_q": {}
    }
    
    msg = "📝 <b>Create Survey</b>\n\nPlease enter the <b>Title</b> of your survey:"
    if query:
        await query.edit_message_text(msg, parse_mode="HTML")
    else:
        await update.message.reply_html(msg)
    return TITLE

async def title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["survey"]["title"] = update.message.text.strip()
    await update.message.reply_html(
        "📝 Enter a <b>Description</b> for your survey (or skip):",
        reply_markup=skip_keyboard()
    )
    return DESCRIPTION

async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["survey"]["description"] = ""
    else:
        context.user_data["survey"]["description"] = update.message.text.strip()

    msg = "🕵️ Should responses be <b>Anonymous</b>?"
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, parse_mode="HTML", reply_markup=anonymous_keyboard())
    else:
        await update.message.reply_html(msg, reply_markup=anonymous_keyboard())
    return ANONYMOUS

async def anonymous_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    is_anon = query.data == "anon_yes"
    context.user_data["survey"]["is_anonymous"] = is_anon
    
    await query.edit_message_text("❓ <b>Question 1</b>\n\nEnter the text for your question:", parse_mode="HTML")
    return Q_TEXT

async def question_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["survey"]["current_q"] = {
        "text": text,
        "type": "",
        "options": []
    }
    
    await update.message.reply_html(
        f"❓ Question: <b>{text}</b>\n\nSelect the <b>Question Type</b>:",
        reply_markup=question_type_keyboard()
    )
    return Q_TYPE

async def question_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    qtype = query.data.replace("qtype_", "")
    curr_q = context.user_data["survey"]["current_q"]
    curr_q["type"] = qtype
    
    if qtype == "yes_no":
        curr_q["options"] = ["Yes", "No"]
        context.user_data["survey"]["questions"].append(curr_q)
        return await show_next_action(query)
    elif qtype == "text":
        curr_q["options"] = []
        context.user_data["survey"]["questions"].append(curr_q)
        return await show_next_action(query)
    else:
        await query.edit_message_text(
            f"⚙️ <b>Question:</b> {curr_q['text']}\n\nEnter option 1:",
            parse_mode="HTML"
        )
        return OPTION_TEXT

async def option_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opt_text = update.message.text.strip()
    curr_q = context.user_data["survey"]["current_q"]
    curr_q["options"].append(opt_text)
    
    opts_list = "\n".join([f"{idx+1}. {o}" for idx, o in enumerate(curr_q["options"])])
    has_enough = len(curr_q["options"]) >= 2
    
    await update.message.reply_html(
        f"⚙️ <b>Question:</b> {curr_q['text']}\n\n<b>Current Options:</b>\n{opts_list}\n\nEnter option {len(curr_q['options']) + 1}:",
        reply_markup=add_options_keyboard(has_enough)
    )
    return OPTION_TEXT

async def done_options_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    curr_q = context.user_data["survey"]["current_q"]
    context.user_data["survey"]["questions"].append(curr_q)
    return await show_next_action(query)

async def show_next_action(query):
    q_count = len(query.message.bot_data.get("dummy", [])) if False else 0 # helper
    q_len = len(query.message.chat if hasattr(query, 'chat') else []) # dummy ref
    
    await query.edit_message_text(
        "✅ Question added successfully!\n\nWhat would you like to do next?",
        reply_markup=next_question_keyboard()
    )
    return NEXT_ACTION

async def next_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "next_add":
        q_num = len(context.user_data["survey"]["questions"]) + 1
        await query.edit_message_text(f"❓ <b>Question {q_num}</b>\n\nEnter the question text:", parse_mode="HTML")
        return Q_TEXT
    elif query.data == "next_preview":
        srv = context.user_data["survey"]
        preview = f"📋 <b>Survey Preview</b>\n\n"
        preview += f"<b>Title:</b> {srv['title']}\n"
        if srv['description']:
            preview += f"<b>Description:</b> {srv['description']}\n"
        preview += f"<b>Anonymous:</b> {'Yes' if srv['is_anonymous'] else 'No'}\n\n"
        preview += "<b>Questions:</b>\n"
        
        for idx, q in enumerate(srv["questions"]):
            preview += f"\n{idx+1}. {q['text']} <i>({q['type']})</i>\n"
            for o_idx, opt in enumerate(q["options"]):
                preview += f"   └ {o_idx+1}. {opt}\n"
                
        await query.edit_message_text(preview, parse_mode="HTML", reply_markup=publish_keyboard())
        return CONFIRM_PUBLISH

async def publish_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    srv = context.user_data["survey"]
    survey_id = generate_survey_id()
    creator_id = update.effective_user.id
    
    await database.create_survey(
        survey_id, creator_id, srv["title"], srv["description"], srv["is_anonymous"]
    )
    
    for q_order, q in enumerate(srv["questions"], start=1):
        q_id = await database.add_question(survey_id, q["text"], q["type"], q_order)
        for opt_order, opt_text in enumerate(q["options"], start=1):
            await database.add_option(q_id, opt_text, opt_order)
            
    bot_info = await context.bot.get_me()
    share_link = f"https://t.me/{bot_info.username}?start=survey_{survey_id}"
    
    success_msg = (
        "🎉 <b>Survey Published Successfully!</b>\n\n"
        f"<b>Title:</b> {srv['title']}\n"
        f"<b>Shareable Link:</b>\n<code>{share_link}</code>"
    )
    await query.edit_message_text(success_msg, parse_mode="HTML", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "❌ Survey creation cancelled."
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg, reply_markup=main_menu_keyboard())
    elif update.message:
        await update.message.reply_html(msg, reply_markup=main_menu_keyboard())
    return ConversationHandler.END

def get_create_survey_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_create_survey, pattern="^menu_create$"),
            CommandHandler("create", start_create_survey)
        ],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_handler)],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler),
                CallbackQueryHandler(description_handler, pattern="^skip_description$")
            ],
            ANONYMOUS: [CallbackQueryHandler(anonymous_handler, pattern="^anon_")],
            Q_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_text_handler)],
            Q_TYPE: [CallbackQueryHandler(question_type_handler, pattern="^qtype_")],
            OPTION_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, option_text_handler),
                CallbackQueryHandler(done_options_handler, pattern="^done_options$")
            ],
            NEXT_ACTION: [CallbackQueryHandler(next_action_handler, pattern="^next_")],
            CONFIRM_PUBLISH: [CallbackQueryHandler(publish_confirm_handler, pattern="^publish_confirm$")]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            CallbackQueryHandler(cancel_handler, pattern="^cancel_creation$")
        ]
    )
