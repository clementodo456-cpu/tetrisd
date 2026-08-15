from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Create Survey", callback_data="menu_create")],
        [
            InlineKeyboardButton("📊 My Surveys", callback_data="menu_mysurveys"),
            InlineKeyboardButton("📈 Results", callback_data="menu_results")
        ],
        [InlineKeyboardButton("❓ Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def question_type_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔘 Single Choice", callback_data="qtype_single")],
        [InlineKeyboardButton("☑️ Multiple Choice", callback_data="qtype_multiple")],
        [InlineKeyboardButton("✅/❌ Yes / No", callback_data="qtype_yes_no")],
        [InlineKeyboardButton("💬 Short Text Answer", callback_data="qtype_text")],
        [InlineKeyboardButton("❌ Cancel Creation", callback_data="cancel_creation")]
    ]
    return InlineKeyboardMarkup(keyboard)

def anonymous_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("👤 Public (Show Users)", callback_data="anon_no"),
            InlineKeyboardButton("🕵️ Anonymous", callback_data="anon_yes")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def skip_keyboard():
    keyboard = [[InlineKeyboardButton("⏭ Skip Description", callback_data="skip_description")]]
    return InlineKeyboardMarkup(keyboard)

def add_options_keyboard(has_enough_options: bool):
    keyboard = []
    if has_enough_options:
        keyboard.append([InlineKeyboardButton("✅ Done with Options", callback_data="done_options")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_creation")])
    return InlineKeyboardMarkup(keyboard)

def next_question_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Add Another Question", callback_data="next_add")],
        [InlineKeyboardButton("👁 Preview & Finish", callback_data="next_preview")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_creation")]
    ]
    return InlineKeyboardMarkup(keyboard)

def publish_keyboard():
    keyboard = [
        [InlineKeyboardButton("🚀 Publish Survey", callback_data="publish_confirm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_creation")]
    ]
    return InlineKeyboardMarkup(keyboard)

def survey_item_keyboard(survey_id: str, is_closed: bool, bot_username: str):
    status_btn = (
        InlineKeyboardButton("🔓 Reopen Survey", callback_data=f"toggle_{survey_id}")
        if is_closed else
        InlineKeyboardButton("🔒 Close Survey", callback_data=f"toggle_{survey_id}")
    )
    share_url = f"https://t.me/share/url?url=https://t.me/{bot_username}?start=survey_{survey_id}&text=Take%20this%20survey!"
    keyboard = [
        [
            InlineKeyboardButton("📈 Results", callback_data=f"viewres_{survey_id}"),
            InlineKeyboardButton("🔗 Share", url=share_url)
        ],
        [status_btn, InlineKeyboardButton("🗑 Delete", callback_data=f"delete_{survey_id}")],
        [InlineKeyboardButton("🔙 Back to My Surveys", callback_data="menu_mysurveys")]
    ]
    return InlineKeyboardMarkup(keyboard)
