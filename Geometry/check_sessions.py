import sqlite3
import json
import uuid
from session_db import SessionDB
from session import Session

# הגדרת הנתיב למסד הנתונים
db_path = "sessions.db"

def load_all_sessions():
    """ טוען את כל הסשנים השמורים במסד הנתונים ומציג אותם """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, data FROM sessions")
        rows = cursor.fetchall()

        if not rows:
            print("⚠️ לא נמצאו סשנים במסד הנתונים.")
            return

        print("\n📌 רשימת הסשנים השמורים במסד הנתונים:")
        for session_id, data in rows:
            session_data = json.loads(data)  # המרת ה-JSON למילון

            print(f"\n🔹 מזהה סשן: {session_id}")
            print(f"   אינטראקציות: {session_data.get('interactions', [])}")
            print(f"   פידבק: {session_data.get('feedback', None)}")
            print(f"   סוג משולש שסומן: {session_data.get('triangle_type', None)}")
            print(f"   משפטים שסייעו: {session_data.get('helpful_theorems', [])}")


##יצירת סשנים פיקטיביים לפי כמות שהמשתמש רוצה
def generate_fake_session_interactively():
        print("\n🎭 יצירת סשן פיקטיבי:")

        session = Session()

        # הוספת אינטראקציות
        while True:
            qid = input("🔹 הזן מספר שאלה (או הקלד 'end' לסיום): ").strip()
            if qid.lower() == "end":
                break
            if not qid.isdigit():
                print("⚠️ מספר שאלה לא חוקי.")
                continue

            aid = input("   🔸 הזן מספר תשובה לשאלה זו: ").strip()
            if not aid.isdigit():
                print("⚠️ מספר תשובה לא חוקי.")
                continue

            session.add_interaction(int(qid), int(aid))

        # פידבק
        print("\n📌 הזן פידבק:")
        print("(4) לא הצלחתי הפעם")
        print("(5) הצלחתי תודה")
        print("(6) התקדמתי אבל אנסה תרגיל חדש")
        print("(7) חזרה לתרגיל")

        while True:
            feedback = input("👉 מספר פידבק: ").strip()
            if feedback in {"4", "5", "6", "7"}:
                session.set_feedback(int(feedback))
                break
            print("⚠️ פידבק לא תקין.")

        # סוגי משולשים
        triangle_input = input("🔺 הזן סוגי משולשים מופרדים ברווח (או השאר ריק לדילוג): ").strip()
        if triangle_input:
            try:
                types = [int(tid) for tid in triangle_input.split() if tid in {"0", "1", "2", "3"}]
                session.set_triangle_type(types)
            except Exception:
                print("⚠️ קלט לא תקין, מדלגים על משולשים.")

        # משפטים
        theorems_input = input("🧠 הזן מספרי משפטים שסייעו (מופרדים ברווח, או 0 לדילוג): ").strip()
        if theorems_input != "0":
            try:
                ids = [int(tid) for tid in theorems_input.split()]
                session.set_helpful_theorems(ids)
            except:
                print("⚠️ קלט לא תקין, לא יישמרו משפטים.")

        # שכפול סשנים
        while True:
            n = input("🔁 כמה עותקים של הסשן להכניס למסד הנתונים? ").strip()
            if n.isdigit() and int(n) > 0:
                n = int(n)
                break
            print("⚠️ מספר לא תקין.")

        db = SessionDB()
        for _ in range(n):
            new_session = Session()  # נשתמש בהעתק כדי לייצר מזהה חדש
            new_session.interactions = session.interactions.copy()
            new_session.feedback = session.feedback
            new_session.triangle_type = session.triangle_type.copy() if session.triangle_type else None
            new_session.helpful_theorems = session.helpful_theorems.copy()
            db.save_session(new_session)

        print(f"\n✅ הוזנו {n} סשנים פיקטיביים למסד הנתונים.")




## שכפול סשנים קיימים לפי כמות שהמשתמש רוצה
def clone_existing_session(db_path="sessions.db"):
    session_id_to_clone = input("🔎 הזן מזהה סשן לשכפול: ").strip()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # חיפוש הסשן לפי מזהה
        cursor.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id_to_clone,))
        row = cursor.fetchone()

        if not row:
            print("❌ סשן עם המזהה הזה לא נמצא.")
            return

        # המרת ה־JSON לאובייקט
        session_data = json.loads(row[0])

        # שאל כמה עותקים לשכפל
        try:
            n = int(input("🔁 כמה עותקים לשכפל? "))
        except ValueError:
            print("⚠️ מספר לא תקין.")
            return

        # הכנסת עותקים
        inserted = 0
        for _ in range(n):
            new_id = str(uuid.uuid4())
            session_data_copy = session_data.copy()
            session_data_copy["session_id"] = new_id

            cursor.execute("INSERT INTO sessions (session_id, data) VALUES (?, ?)",
                           (new_id, json.dumps(session_data_copy, ensure_ascii=False)))

            inserted += 1

        conn.commit()

        print(f"\n✅ {inserted} סשנים שוכפלו בהצלחה מתוך הסשן {session_id_to_clone}.")


def delete_session_by_id(db_path="sessions.db"):
    """ מוחק סשן בודד לפי מזהה (session_id) ממסד הנתונים """
    sid = input("🗑️ הזן מזהה סשן למחיקה: ").strip()
    if not sid:
        print("⚠️ לא הוזן מזהה.")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            # הפעלת מפתחות זרים (למקרה שיש טבלאות נוספות התלויות בסשן)
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()

            # בדיקה שהסשן קיים
            cursor.execute("SELECT 1 FROM sessions WHERE session_id = ?", (sid,))
            if not cursor.fetchone():
                print("❌ לא נמצא סשן עם המזהה הזה.")
                return

            # אישור מחיקה
            confirm = input(f"‼️ לאשר מחיקה של הסשן {sid}? (y/n): ").strip().lower()
            if confirm != "y":
                print("↩️ פעולה בוטלה.")
                return

            # מחיקה
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (sid,))
            conn.commit()

            if cursor.rowcount and cursor.rowcount > 0:
                print(f"✅ הסשן {sid} נמחק בהצלחה.")
            else:
                print("⚠️ לא בוצעה מחיקה (ייתכן שהמזהה לא קיים).")

    except sqlite3.Error as e:
        print(f"❌ שגיאת מסד נתונים: {e}")

# הפעלת הבדיקה
if __name__ == "__main__":
    print("\n📋 תפריט:")
    print("1. הצגת סשנים קיימים")
    print("2. יצירת סשן פיקטיבי חדש")
    print("3. שכפול סשן קיים")
    print("4. מחיקת סשן לפי מזהה")

    choice = input("👉 בחר פעולה (1/2/3/4): ").strip()

    if choice == "1":
        load_all_sessions()
    elif choice == "2":
        generate_fake_session_interactively()
    elif choice == "3":
        clone_existing_session()
    elif choice == "4":  # ← חדש
        delete_session_by_id(db_path)
    else:
        print("⚠️ בחירה לא תקפה.")

