import sys
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)

import config
import database
from handlers.start import start_command, help_command
from handlers.create_survey import get_create_survey_handler
from handlers.take_survey import handle_taking_callbacks, text_answer_handler
from handlers.my_surveys import my_surveys_handler, survey_management_callback
from handlers.results import view_results_handler
from handlers.admin import admin_command, broadcast_command

async def post_init(application):
    await database.init_db()

def main():
    if not config.BOT_TOKEN:
        config.logger.critical("Bot token missing! Please set BOT_TOKEN in .env")
        sys.exit(1)

    app = ApplicationBuilder().token(config.BOT_TOKEN).post_init(post_init).build()

    # Conversation Handlers
    app.add_handler(get_create_survey_handler())

    # Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("mysurveys", my_surveys_handler))
    app.add_handler(CommandHandler("results", view_results_handler))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    # Menu Callbacks
    app.add_handler(CallbackQueryHandler(help_command, pattern="^menu_help$"))
    app.add_handler(CallbackQueryHandler(my_surveys_handler, pattern="^menu_mysurveys$"))
    app.add_handler(CallbackQueryHandler(view_results_handler, pattern="^menu_results$"))

    # Survey Taking & Management Callbacks
    app.add_handler(CallbackQueryHandler(handle_taking_callbacks, pattern="^(start_taking_|opt_)"))
    app.add_handler(CallbackQueryHandler(survey_management_callback, pattern="^(toggle_|delete_)"))
    app.add_handler(CallbackQueryHandler(view_results_handler, pattern="^viewres_"))

    # Text message fallback for text-question taking
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_answer_handler))

    config.logger.info("Survey Creator Bot running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
