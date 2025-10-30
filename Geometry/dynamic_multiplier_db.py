import sqlite3
from session_db import SessionDB
import json


session_db = SessionDB("sessions.db")
sessions = session_db.load_all_sessions()
print(f"🔍 נטענו {len(sessions)} סשנים מה־DB.")


##בדיקה לטבלאות
# def check_tables(db_path="geometry_learning.db"):
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
#     tables = cursor.fetchall()
#     conn.close()
#
#     print("\n📋 רשימת טבלאות במסד הנתונים:")
#     for table in tables:
#         print("🔸", table[0])




## בדיקה לראות שנטענו סשנים
def preview_sessions_from_db():
    session_db = SessionDB("sessions.db")
    sessions = session_db.load_all_sessions()

    if not sessions:
        print("⚠️ לא נמצאו סשנים.")
        return

    for i, session in enumerate(sessions, 1):
        print(f"\n📄 סשן {i}:")
        print(json.dumps(session, indent=4, ensure_ascii=False))


## יצירת הטבלה של המשקולות הדינאמיות
def create_dynamic_multipliers_table(db_path="geometry_learning.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # הפעלת תמיכה במפתחות זרים
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DynamicAnswerMultipliers (
        question_id INTEGER,
        triangle_id INTEGER,
        answer_id INTEGER,
        baseline_multiplier REAL NOT NULL,
        dynamic_multiplier REAL,  -- יכול להיות null
        session_count_total INTEGER DEFAULT 0,
        session_count_with_triangle INTEGER DEFAULT 0,
        PRIMARY KEY (question_id, triangle_id, answer_id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ טבלת DynamicAnswerMultipliers נוצרה בהצלחה (עם answer_id מספרי בלבד).")

##לטעון את הנתונים המקוריים מהטבלה הקשיחה והמקורית
def load_initial_multipliers(db_path="geometry_learning.db"):
    """
    טוען את כל הרשומות מטבלת InitialAnswerMultipliers ומחזיר רשימה של טפלות:
    (question_id, triangle_id, answer_type, multiplier)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT question_id, triangle_id, answer_type, multiplier 
        FROM InitialAnswerMultipliers
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def populate_dynamic_multipliers_from_baseline(db_path="geometry_learning.db"):
    """
    מכניס את כל הנתונים מטבלת InitialAnswerMultipliers לתוך DynamicAnswerMultipliers
    לאחר מיפוי התשובות למספרים, ומתעלם משורות עם multiplier == 0 או 1
    """
    answer_mapping = {
        "לא": 0,
        "כן": 1,
        "לא יודע": 2,
        "כנראה": 3
    }

    baseline_data = load_initial_multipliers(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted_count = 0

    for question_id, triangle_id, answer_text, multiplier in baseline_data:


        answer_id = answer_mapping.get(answer_text)
        if answer_id is None:
            print(f"⚠️ תשובה לא מזוהה: {answer_text}")
            continue

        cursor.execute("""
            INSERT OR IGNORE INTO DynamicAnswerMultipliers (
                question_id, triangle_id, answer_id, baseline_multiplier,
                dynamic_multiplier, session_count_total, session_count_with_triangle
            ) VALUES (?, ?, ?, ?, NULL, 0, 0)
        """, (question_id, triangle_id, answer_id, multiplier))

        inserted_count += 1

    conn.commit()
    conn.close()

    print(f"✅ הוזנו {inserted_count} רשומות לטבלת DynamicAnswerMultipliers.")


def print_dynamic_table(db_path="geometry_learning.db"):
    """
    מדפיסה את תוכן הטבלה הדינאמית לבדיקת תקינות
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM DynamicAnswerMultipliers")
    rows = cursor.fetchall()

    if not rows:
        print("⚠️ הטבלה ריקה.")
    else:
        # שליפת שמות העמודות
        column_names = [description[0] for description in cursor.description]
        print(f"\n📊 נמצאו {len(rows)} רשומות בטבלה DynamicAnswerMultipliers:\n")
        print(" | ".join(column_names))
        print("-" * 80)
        for row in rows:
            print(" | ".join(str(cell) for cell in row))

    conn.close()


##עדכון כמות הסשנים שבהם הצירוף הופיע
def update_session_counts_in_dynamic_table(sessions, db_path="geometry_learning.db"):
    """
    מעדכנת את טבלת DynamicAnswerMultipliers לפי נתוני הסשנים:
    - session_count_total: כמה פעמים הופיע צירוף שאלה-תשובה בסשנים עם triangle_type קיים.
    - session_count_with_triangle: כמה פעמים הופיע גם הצירוף וגם triangle_id תואם למה שהוזן בסשן.
    """

    # מונה של (question_id, answer_id) -> כמה פעמים הופיע
    total_counts = {}

    # מונה של (question_id, triangle_id, answer_id) -> כמה פעמים הופיע יחד עם המשולש
    triangle_specific_counts = {}

    for session in sessions:
        triangle_types = session.get("triangle_type")
        if not triangle_types:
            continue  # מתעלמים מסשנים בלי משולש

        interactions = session.get("interactions", [])
        for interaction in interactions:
            qid = interaction["question_id"]
            aid = interaction["answer_id"]

            total_counts[(qid, aid)] = total_counts.get((qid, aid), 0) + 1

            for triangle_id in triangle_types:
                key = (qid, triangle_id, aid)
                triangle_specific_counts[key] = triangle_specific_counts.get(key, 0) + 1

    # עדכון טבלת ה־DB לפי המונים
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated = 0
    for (qid, triangle_id, aid), count in triangle_specific_counts.items():
        total = total_counts.get((qid, aid), 0)
        cursor.execute("""
            UPDATE DynamicAnswerMultipliers
            SET session_count_total = ?, session_count_with_triangle = ?
            WHERE question_id = ? AND triangle_id = ? AND answer_id = ?
        """, (total, count, qid, triangle_id, aid))
        updated += 1

    conn.commit()
    conn.close()

    print(f"✅ עודכנו {updated} רשומות בטבלת DynamicAnswerMultipliers עם נתוני סשנים.")


##פונקציה שמעדכנת את המשקלים הדינאמיים
def update_dynamic_multipliers_values(db_path="geometry_learning.db"):
    """
    מעדכנת את השדה dynamic_multiplier בטבלת DynamicAnswerMultipliers לפי חישוב אמפירי מהסשנים.
    תנאים לעדכון:
    - session_count_total מעל סף (threshold)
    - baseline_multiplier שונה מ־0 ו־1
    - רמת האמון האמפירית מתורגמת ל־target לפי scale_factor
    - אם empirical == 1 → לא נוריד את המשקל לעולם
    """
    alpha = 0.25
    scale_factor = 1.5
    threshold = 10

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT question_id, triangle_id, answer_id,
               baseline_multiplier, session_count_total, session_count_with_triangle
        FROM DynamicAnswerMultipliers
    """)
    rows = cursor.fetchall()

    updated_count = 0
    for qid, tid, aid, baseline, total, with_triangle in rows:
        if total < threshold or baseline in (0, 1):
            continue

        empirical = with_triangle / total

        if baseline > 1:
            target = max(1, empirical * scale_factor)
        elif baseline < 1:
            target = min(1, empirical * scale_factor)
        else:
            target = 1  # תאורטית לא נגיע לכאן כי סיננו baseline == 1

        updated = baseline + alpha * (target - baseline)

        # הגנה: לא להוריד אם יש התאמה מושלמת
        if empirical == 1 and updated < baseline:
            updated = baseline

        cursor.execute("""
            UPDATE DynamicAnswerMultipliers
            SET dynamic_multiplier = ?
            WHERE question_id = ? AND triangle_id = ? AND answer_id = ?
        """, (updated, qid, tid, aid))

        updated_count += 1

    conn.commit()
    conn.close()
    print(f"✅ עודכנו {updated_count} משקלים דינאמיים בטבלה DynamicAnswerMultipliers.")





if __name__ == "__main__":
    create_dynamic_multipliers_table()
    populate_dynamic_multipliers_from_baseline()
    update_session_counts_in_dynamic_table(sessions)
    update_dynamic_multipliers_values()  # קריאה פשוטה – הערכים בפנים
    print_dynamic_table()

    # print("\n📂 בדיקה שהסשנים זמינים מתוך sessions.db:")
    # preview_sessions_from_db()

