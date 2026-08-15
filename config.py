import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("SurveyBot")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable missing!")

DATABASE_PATH = os.getenv("DATABASE_PATH", "surveys.db").strip()

# Parse Admin IDs into list of integers
raw_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [
    int(admin_id.strip())
    for admin_id in raw_admins.split(",")
    if admin_id.strip().isdigit()
]
