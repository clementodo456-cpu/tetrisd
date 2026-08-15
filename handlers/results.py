from telegram import Update
from telegram.ext import ContextTypes
import database
from utils.helpers import create_progress_bar
from utils.keyboards import main_menu_keyboard

async def view_results_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, survey_id: str = None):
    query = update.callback_query
    if query:
        await query.answer()
        if not survey_id and query.data.startswith("viewres_"):
            survey_id = query.data.replace("viewres_", "")

    if not survey_id:
        if update.message and context.args:
            survey_id = context.args[0]
        else:
            msg = "⚠️ Please specify a survey ID or use /mysurveys to select one."
            if query:
                await query.edit_message_text(msg, reply_markup=main_menu_keyboard())
            else:
                await update.message.reply_html(msg)
            return

    srv = await database.get_survey(survey_id)
    if not srv:
        msg = "⚠️ Survey not found."
        if query:
            await query.edit_message_text(msg, reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_html(msg)
        return

    total_resp, results = await database.get_survey_results(survey_id)
    
    output = f"📈 <b>Results for: {srv['title']}</b>\n"
    output += f"Total Respondents: <b>{total_resp}</b>\n\n"
    
    for idx, q in enumerate(results, start=1):
        output += f"<b>Q{idx}: {q['text']}</b>\n"
        if q["type"] in ["single", "multiple", "yes_no"]:
            for opt in q["options"]:
                pct = (opt["count"] / total_resp * 100) if total_resp > 0 else 0
                bar = create_progress_bar(pct)
                output += f"  └ {opt['text']}\n    {bar} ({opt['count']} votes)\n"
        else:
            output += f"  💬 <i>Text Answers ({len(q['text_answers'])}):</i>\n"
            for ans in q["text_answers"][:5]: # Show first 5
                output += f"   • {ans}\n"
        output += "\n"

    if query:
        await query.edit_message_text(output, parse_mode="HTML", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_html(output, reply_markup=main_menu_keyboard())
