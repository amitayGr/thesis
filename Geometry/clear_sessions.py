import sqlite3

def clear_all_sessions(db_path="sessions.db"):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions")
        conn.commit()
        print("🧹 כל הסשנים נמחקו מהמסד בהצלחה.")

if __name__ == "__main__":
    print("⚠️  פעולה זו תמחק את *כל* הסשנים מהמערכת.")
    password = input("🔐 האם אתה בטוח? הזן סיסמה כדי להמשיך: ")

    if password == "190598":
        clear_all_sessions()
    else:
        print("🚫 סיסמה שגויה. הסשנים לא נמחקו.")
