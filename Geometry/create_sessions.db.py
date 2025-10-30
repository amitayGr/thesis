import sqlite3

# הגדרת שם קובץ מסד הנתונים
db_path = "sessions.db"

# ניסיון לפתוח חיבור וליצור את ה-DB
try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                data TEXT
            )
        ''')
        conn.commit()
        print("✅ מסד הנתונים sessions.db נוצר בהצלחה!")
except Exception as e:
    print(f"❌ שגיאה ביצירת מסד הנתונים: {e}")
