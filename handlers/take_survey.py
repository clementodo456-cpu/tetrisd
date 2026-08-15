from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database

async def initiate_take_survey(update: Update, context: ContextTypes.DEFAULT_TYPE, survey_id: str):
    user_id = update.effective_user.id
    survey = await database.get_survey(survey_id)
    
    if not survey:
        await update.message.reply_html("⚠️ Survey not found or has been deleted.")
        return

    if survey["is_closed"]:
        await update.message.reply_html("🔒 This survey is closed and no longer accepting responses.")
        return

    if await database.has_user_responded(survey_id, user_id):
        await update.message.reply_html("⚠️ You have already completed this survey!")
        return

    questions = await database.get_survey_questions(survey_id)
    if not questions:
        await update.message.reply_html("⚠️ This survey has no questions.")
        return

    context.user_data["taking"] = {
        "survey_id": survey_id,
        "q_index": 0,
        "questions": questions,
        "answers": {}
    }

    start_text = (
        f"📝 <b>{survey['title']}</b>\n\n"
        f"{survey['description'] or 'No description provided.'}\n\n"
        f"Total Questions: {len(questions)}\n"
        f"Anonymous: {'Yes' if survey['is_anonymous'] else 'No'}\n\n"
        "Ready to begin?"
    )
    keyboard = [[InlineKeyboardButton("▶ Begin Survey", callback_data=f"start_taking_{survey_id}")]]
    await update.message.reply_html(start_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_taking_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    taking = context.user_data.get("taking")
    if not taking:
        await query.edit_message_text("⚠️ Survey session expired. Please open the survey link again.")
        return

    if data.startswith("start_taking_"):
        await render_question(query, context)
        return

    curr_q = taking["questions"][taking["q_index"]]
    q_id = curr_q["id"]

    if data.startswith("opt_single_"):
        opt_id = int(data.split("_")[2])
        taking["answers"][q_id] = {"options": [opt_id]}
        taking["q_index"] += 1
        await render_question(query, context)

    elif data.startswith("opt_multi_toggle_"):
        opt_id = int(data.split("_")[3])
        if q_id not in taking["answers"]:
            taking["answers"][q_id] = {"options": []}
        
        opts = taking["answers"][q_id]["options"]
        if opt_id in opts:
            opts.remove(opt_id)
        else:
            opts.append(opt_id)
        await render_question(query, context)

    elif data.startswith("opt_multi_submit_"):
        if q_id not in taking["answers"] or not taking["answers"][q_id]["options"]:
            await query.answer("Please select at least one option!", show_alert=True)
            return
        taking["q_index"] += 1
        await render_question(query, context)

async def render_question(query, context: ContextTypes.DEFAULT_TYPE):
    taking = context.user_data["taking"]
    q_index = taking["q_index"]
    questions = taking["questions"]
    
    if q_index >= len(questions):
        # Save all responses
        user_id = query.from_user.id
        await database.save_response(taking["survey_id"], user_id, taking["answers"])
        context.user_data.pop("taking", None)
        await query.edit_message_text("🎉 <b>Thank you! Your responses have been recorded.</b>", parse_mode="HTML")
        return

    curr_q = questions[q_index]
    q_id = curr_q["id"]
    q_type = curr_q["question_type"]
    
    text = f"<b>Question {q_index + 1} of {len(questions)}</b>\n\n{curr_q['question_text']}"
    keyboard = []

    if q_type in ["single", "yes_no"]:
        opts = await database.get_question_options(q_id)
        for opt in opts:
            keyboard.append([InlineKeyboardButton(opt["option_text"], callback_data=f"opt_single_{opt['id']}")])
    elif q_type == "multiple":
        opts = await database.get_question_options(q_id)
        selected = taking["answers"].get(q_id, {}).get("options", [])
        for opt in opts:
            prefix = "☑️ " if opt["id"] in selected else "🔲 "
            keyboard.append([InlineKeyboardButton(f"{prefix}{opt['option_text']}", callback_data=f"opt_multi_toggle_{opt['id']}")])
        keyboard.append([InlineKeyboardButton("✅ Submit Answer", callback_data=f"opt_multi_submit_{q_id}")])
    elif q_type == "text":
        text += "\n\n<i>💬 Please type and send your short text answer below:</i>"

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

async def text_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    taking = context.user_data.get("taking")
    if not taking:
        return

    q_index = taking["q_index"]
    questions = taking["questions"]
    
    if q_index < len(questions):
        curr_q = questions[q_index]
        if curr_q["question_type"] == "text":
            taking["answers"][curr_q["id"]] = {"text": update.message.text.strip()}
            taking["q_index"] += 1
            
            # Helper trick to reuse query rendering
            class DummyQuery:
                def __init__(self, msg, user):
                    self.message = msg
                    self.from_user = user
                async def edit_message_text(self, text, parse_mode=None, reply_markup=None):
                    await self.message.reply_html(text, reply_markup=reply_markup)
                async def answer(self, text="", show_alert=False):
                    pass

            dummy = DummyQuery(update.message, update.effective_user)
            await render_question(dummy, context)
