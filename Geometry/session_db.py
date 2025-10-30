import sqlite3
import json

class SessionDB:
    def __init__(self, db_path="sessions.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """יוצרת את טבלת המסלולים אם היא לא קיימת"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    data TEXT  -- JSON שמכיל את המסלול
                )
            ''')
            conn.commit()

    def save_session(self, session):
        """שומר מסלול חדש במסד הנתונים"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (session_id, data)
                VALUES (?, ?)
            ''', (session.session_id, session.to_json()))
            conn.commit()

    def load_all_sessions(self):
        """טוען את כל המסלולים מה-DB"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM sessions")
            rows = cursor.fetchall()
            return [json.loads(row[0]) for row in rows] if rows else []



if __name__ == "__main__":
    db = SessionDB("sessions.db")
    sessions = db.load_all_sessions()

    print(f"🔎 נמצאו {len(sessions)} סשנים:\n")

    for i, session in enumerate(sessions, 1):
        print(f"📄 סשן {i}:")
        print(json.dumps(session, indent=4, ensure_ascii=False))
        print("=" * 60)
