"""
Lightweight persistent preference memory — survives across sessions,
distinct from the in-session conversation_memory in StylistAgent.
Stores short rejection/refinement notes so future recommendations
for this user can avoid repeating a disliked pattern.
"""

from src.database.db import get_connection


def init_preferences_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_preference_note(user_id: str, note: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO user_preferences (user_id, note) VALUES (?, ?)",
        (user_id, note),
    )
    conn.commit()
    conn.close()


def get_recent_preferences(user_id: str, limit: int = 5) -> list[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT note FROM user_preferences WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]
