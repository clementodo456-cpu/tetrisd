import aiosqlite
from config import DATABASE_PATH, logger

async def init_db():
    """Initialize database tables."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        
        # Users Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Surveys Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id TEXT PRIMARY KEY,
                creator_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                is_anonymous INTEGER DEFAULT 0,
                is_closed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(creator_id) REFERENCES users(user_id)
            );
        """)
        
        # Questions Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                question_order INTEGER NOT NULL,
                FOREIGN KEY(survey_id) REFERENCES surveys(id) ON DELETE CASCADE
            );
        """)
        
        # Options Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                option_text TEXT NOT NULL,
                option_order INTEGER NOT NULL,
                FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
        """)
        
        # Responses Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(survey_id, user_id),
                FOREIGN KEY(survey_id) REFERENCES surveys(id) ON DELETE CASCADE
            );
        """)
        
        # Answers Table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                option_id INTEGER,
                text_answer TEXT,
                FOREIGN KEY(response_id) REFERENCES responses(id) ON DELETE CASCADE,
                FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
        """)
        
        await db.commit()
        logger.info("Database initialized successfully.")

async def add_user(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()

async def create_survey(survey_id: str, creator_id: int, title: str, description: str, is_anonymous: bool):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO surveys (id, creator_id, title, description, is_anonymous) VALUES (?, ?, ?, ?, ?)",
            (survey_id, creator_id, title, description, 1 if is_anonymous else 0)
        )
        await db.commit()

async def add_question(survey_id: str, question_text: str, question_type: str, order: int) -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO questions (survey_id, question_text, question_type, question_order) VALUES (?, ?, ?, ?)",
            (survey_id, question_text, question_type, order)
        )
        await db.commit()
        return cursor.lastrowid

async def add_option(question_id: int, option_text: str, order: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO options (question_id, option_text, option_order) VALUES (?, ?, ?)",
            (question_id, option_text, order)
        )
        await db.commit()

async def get_survey(survey_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM surveys WHERE id = ?", (survey_id,)) as cursor:
            return await cursor.fetchone()

async def get_survey_questions(survey_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM questions WHERE survey_id = ? ORDER BY question_order ASC", (survey_id,)
        ) as cursor:
            return await cursor.fetchall()

async def get_question_options(question_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM options WHERE question_id = ? ORDER BY option_order ASC", (question_id,)
        ) as cursor:
            return await cursor.fetchall()

async def get_user_surveys(creator_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT s.*, COUNT(r.id) as response_count
            FROM surveys s
            LEFT JOIN responses r ON s.id = r.survey_id
            WHERE s.creator_id = ?
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """
        async with db.execute(query, (creator_id,)) as cursor:
            return await cursor.fetchall()

async def toggle_survey_status(survey_id: str, is_closed: bool):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE surveys SET is_closed = ? WHERE id = ?", (1 if is_closed else 0, survey_id))
        await db.commit()

async def delete_survey(survey_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("DELETE FROM surveys WHERE id = ?", (survey_id,))
        await db.commit()

async def has_user_responded(survey_id: str, user_id: int) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT 1 FROM responses WHERE survey_id = ? AND user_id = ?", (survey_id, user_id)) as cursor:
            return await cursor.fetchone() is not None

async def save_response(survey_id: str, user_id: int, answers: dict):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        cursor = await db.execute(
            "INSERT INTO responses (survey_id, user_id) VALUES (?, ?)", (survey_id, user_id)
        )
        response_id = cursor.lastrowid
        
        for q_id, ans in answers.items():
            if ans.get("options"):
                for opt_id in ans["options"]:
                    await db.execute(
                        "INSERT INTO answers (response_id, question_id, option_id) VALUES (?, ?, ?)",
                        (response_id, q_id, opt_id)
                    )
            elif ans.get("text"):
                await db.execute(
                    "INSERT INTO answers (response_id, question_id, text_answer) VALUES (?, ?, ?)",
                    (response_id, q_id, ans["text"])
                )
        await db.commit()

async def get_survey_results(survey_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Total responses
        async with db.execute("SELECT COUNT(*) as total FROM responses WHERE survey_id = ?", (survey_id,)) as cursor:
            total_resp = (await cursor.fetchone())["total"]
            
        questions = await get_survey_questions(survey_id)
        results = []
        
        for q in questions:
            q_data = {
                "id": q["id"],
                "text": q["question_text"],
                "type": q["question_type"],
                "options": [],
                "text_answers": []
            }
            
            if q["question_type"] in ["single", "multiple", "yes_no"]:
                opts = await get_question_options(q["id"])
                for opt in opts:
                    async with db.execute(
                        "SELECT COUNT(*) as cnt FROM answers WHERE question_id = ? AND option_id = ?",
                        (q["id"], opt["id"])
                    ) as cursor:
                        cnt = (await cursor.fetchone())["cnt"]
                    q_data["options"].append({
                        "id": opt["id"],
                        "text": opt["option_text"],
                        "count": cnt
                    })
            else:
                async with db.execute(
                    "SELECT text_answer FROM answers WHERE question_id = ? AND text_answer IS NOT NULL",
                    (q["id"],)
                ) as cursor:
                    rows = await cursor.fetchall()
                    q_data["text_answers"] = [r["text_answer"] for r in rows]
                    
            results.append(q_data)
            
        return total_resp, results

async def get_admin_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM surveys") as c2:
            total_surveys = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM responses") as c3:
            total_responses = (await c3.fetchone())[0]
        return total_users, total_surveys, total_responses

async def get_all_user_ids():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]
