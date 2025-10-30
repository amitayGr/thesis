import sqlite3
from session_db import SessionDB
import json


session_db = SessionDB("sessions.db")
sessions = session_db.load_all_sessions()
print(f"🔍 נטענו {len(sessions)} סשנים מה־DB.")


#בדיקה לטבלאות
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
#
#
#
#
# ## בדיקה לראות שנטענו סשנים
# def preview_sessions_from_db():
#     session_db = SessionDB("sessions.db")
#     sessions = session_db.load_all_sessions()
#
#     if not sessions:
#         print("⚠️ לא נמצאו סשנים.")
#         return
#
#     for i, session in enumerate(sessions, 1):
#         print(f"\n📄 סשן {i}:")
#         print(json.dumps(session, indent=4, ensure_ascii=False))


def create_theorem_scores_table(db_path="geometry_learning.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # הפעלת תמיכה במפתחות זרים אם תרצה בעתיד להשתמש בזה
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TheoremScores (
        question_id INTEGER,
        answer_id INTEGER,
        theorem_id INTEGER,
        count_total INTEGER DEFAULT 0,
        count_helpful INTEGER DEFAULT 0,
        score REAL ,
        PRIMARY KEY (question_id, answer_id, theorem_id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ טבלת TheoremScores נוצרה בהצלחה עם ערכי ברירת מחדל.")



def populate_theorem_scores_initial(db_path="geometry_learning.db"):
    """
    מאתחל את הטבלה TheoremScores עם כל הצירופים האפשריים של שאלה, תשובה ומשפט.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0

    for question_id in range(1, 29):  # כולל 28
        for answer_id in range(0, 4):  # כולל 3
            for theorem_id in range(1, 64):  # כולל 63
                cursor.execute("""
                    INSERT OR IGNORE INTO TheoremScores (
                        question_id, answer_id, theorem_id,
                        count_total, count_helpful, score
                    ) VALUES (?, ?, ?, 0, 0, 0)
                """, (question_id, answer_id, theorem_id))
                inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ הוזנו {inserted} רשומות ראשוניות לטבלת TheoremScores.")

def print_theorem_scores_table(db_path="geometry_learning.db"):
        """
        מדפיסה את 300 הרשומות הראשונות מטבלת TheoremScores לצורכי בדיקה.
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM TheoremScores")
        rows = cursor.fetchall()

        if not rows:
            print("⚠️ הטבלה TheoremScores ריקה.")
        else:
            column_names = [description[0] for description in cursor.description]
            print(f"\n📊 נמצאו {len(rows)} רשומות בטבלה TheoremScores.\n")
            print(" | ".join(column_names))
            print("-" * 100)
            for row in rows[:300]:  # מדפיס את 300 הראשונים
                print(" | ".join(str(cell) for cell in row))

        conn.close()

def update_counts_from_sessions(sessions, db_path="geometry_learning.db"):
    """
    מעדכן את count_total ו־count_helpful בטבלת TheoremScores לפי נתוני הסשנים.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    total_updated = 0
    helpful_updated = 0

    for session in sessions:
        interactions = session.get("interactions", [])
        helpful_theorems = session.get("helpful_theorems", [])

        for interaction in interactions:
            qid = interaction.get("question_id")
            aid = interaction.get("answer_id")

            # עדכון count_total לכל המשפטים עבור הצירוף הזה
            for theorem_id in range(1, 64):
                cursor.execute("""
                    UPDATE TheoremScores
                    SET count_total = count_total + 1
                    WHERE question_id = ? AND answer_id = ? AND theorem_id = ?
                """, (qid, aid, theorem_id))
                total_updated += 1

            # אם היו helpful_theorems – נעדכן רק להם את count_helpful
            for tid in helpful_theorems:
                cursor.execute("""
                    UPDATE TheoremScores
                    SET count_helpful = count_helpful + 1
                    WHERE question_id = ? AND answer_id = ? AND theorem_id = ?
                """, (qid, aid, tid))
                helpful_updated += 1

    conn.commit()
    conn.close()
    print(f"✅ עודכנו {total_updated} ערכי count_total ו־{helpful_updated} ערכי count_helpful.")


def update_score_column(db_path="geometry_learning.db"):
    """
    מעדכנת את עמודת score בטבלת TheoremScores לפי:
    score = count_helpful / count_total
    רק אם count_total > 0
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # שליפת כל השורות עם count_total > 0
    cursor.execute("""
        SELECT question_id, answer_id, theorem_id, count_total, count_helpful
        FROM TheoremScores
        WHERE count_total > 0
    """)
    rows = cursor.fetchall()

    updated = 0
    for qid, aid, tid, total, helpful in rows:
        score = helpful / total
        cursor.execute("""
            UPDATE TheoremScores
            SET score = ?
            WHERE question_id = ? AND answer_id = ? AND theorem_id = ?
        """, (score, qid, aid, tid))
        updated += 1

    conn.commit()
    conn.close()
    print(f"✅ עודכנו {updated} ערכים בעמודת score בטבלת TheoremScores.")




def create_general_helpfulness_table(db_path="geometry_learning.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TheoremGeneralHelpfulness (
        theorem_id INTEGER PRIMARY KEY,
        helpful_session_count INTEGER DEFAULT 0,
        general_helpfulness REAL 
    )
    """)

    conn.commit()
    conn.close()
    print("✅ טבלת TheoremGeneralHelpfulness נוצרה בהצלחה (רק עם theorem_id ו-general_helpfulness).")


def populate_general_helpfulness_table(db_path="geometry_learning.db"):
    """
    מאתחל את טבלת TheoremGeneralHelpfulness עם ערכים התחלתיים:
    helpful_session_count = 0, general_helpfulness = 0.2 לכל המשפטים 1–63.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0
    for theorem_id in range(1, 64):  # כולל 63
        cursor.execute("""
            INSERT OR IGNORE INTO TheoremGeneralHelpfulness (
                theorem_id, helpful_session_count, general_helpfulness
            ) VALUES (?, 0, 0)
        """, (theorem_id,))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ הוזנו {inserted} רשומות לטבלת TheoremGeneralHelpfulness עם ערכים התחלתיים.")


def recompute_helpful_session_count(sessions, db_path="geometry_learning.db"):
    """
    מחשבת מחדש את helpful_session_count בטבלת TheoremGeneralHelpfulness
    על סמך כל הסשנים, ומאפס לפני כן את הטבלה.
    """
    from collections import defaultdict

    # שלב 1: ספירת מופעים מחדש
    helpful_counts = defaultdict(int)

    for session in sessions:
        unique_theorems = set(session.get("helpful_theorems", []))
        for tid in unique_theorems:
            helpful_counts[tid] += 1

    # שלב 2: עדכון בטבלה
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # אפס את כל המונים
    cursor.execute("UPDATE TheoremGeneralHelpfulness SET helpful_session_count = 0")

    updated = 0
    for tid, count in helpful_counts.items():
        cursor.execute("""
            UPDATE TheoremGeneralHelpfulness
            SET helpful_session_count = ?
            WHERE theorem_id = ?
        """, (count, tid))
        updated += 1

    conn.commit()
    conn.close()
    print(f"✅ חושבו מחדש {updated} ערכים של helpful_session_count.")


def update_general_helpfulness(sessions, db_path="geometry_learning.db"):
    """
    מעדכנת את הערך general_helpfulness עבור כל משפט בטבלת TheoremGeneralHelpfulness.
    היחס מחושב כך: helpful_session_count / total_sessions
    """


    total_sessions = len(sessions)
    if total_sessions == 0:
        print("⚠️ אין סשנים לעדכן על פיהם את general_helpfulness.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT theorem_id, helpful_session_count FROM TheoremGeneralHelpfulness")
    rows = cursor.fetchall()

    updated = 0
    for tid, count in rows:
        new_score = count / total_sessions
        cursor.execute("""
            UPDATE TheoremGeneralHelpfulness
            SET general_helpfulness = ?
            WHERE theorem_id = ?
        """, (new_score, tid))
        updated += 1

    conn.commit()
    conn.close()
    print(f"✅ עודכנו {updated} ערכי general_helpfulness בטבלה לפי {total_sessions} סשנים.")

def print_general_helpfulness_table(db_path="geometry_learning.db"):
    """
    מדפיסה את כל הרשומות מטבלת TheoremGeneralHelpfulness.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM TheoremGeneralHelpfulness")
    rows = cursor.fetchall()

    if not rows:
        print("⚠️ הטבלה TheoremGeneralHelpfulness ריקה.")
    else:
        column_names = [description[0] for description in cursor.description]
        print(f"\n📊 נמצאו {len(rows)} רשומות בטבלה TheoremGeneralHelpfulness:\n")
        print(" | ".join(column_names))
        print("-" * 60)
        for row in rows:
            print(" | ".join(str(cell) for cell in row))

    conn.close()





if __name__ == "__main__":
            # check_tables()
            # preview_sessions_from_db()
            # יצירת טבלאות

            create_theorem_scores_table()
            populate_theorem_scores_initial()
            create_general_helpfulness_table()
            populate_general_helpfulness_table()

            # עדכון טבלת TheoremScores
            update_counts_from_sessions(sessions)
            update_score_column()
            print_theorem_scores_table()

            # עדכון טבלת TheoremGeneralHelpfulness
            recompute_helpful_session_count(sessions)
            update_general_helpfulness(sessions)
            print_general_helpfulness_table()


