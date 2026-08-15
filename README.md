# Survey Creator Bot (@tetrisdeestbot)

A feature-rich Telegram Bot built with Python 3.11+, `python-telegram-bot`, and SQLite that allows users to create surveys, customize questions, share them across Telegram chats, and analyze real-time results.

## Features
- **Survey Creation Workflow**: Customizable titles, optional descriptions, anonymous response options, single/multiple choice, Yes/No, and short text input questions.
- **Deep Linking**: Share surveys via unique Telegram links (`t.me/tetrisdeestbot?start=survey_<id>`).
- **Duplicate Prevention**: Tracks respondent user IDs securely.
- **Survey Management**: Reopen, close, or delete surveys at any time.
- **Analytics & Visualizations**: Real-time ASCII progress bar representation of votes and text answer aggregations.
- **Admin Tools**: Statistics panel and global broadcast capabilities.

## Local Setup

1. **Clone Repository**:
   ```bash
   git clone [https://github.com/yourusername/survey-creator-bot.git](https://github.com/yourusername/survey-creator-bot.git)
   cd survey-creator-bot
