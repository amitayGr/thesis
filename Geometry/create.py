import sqlite3

def create_database(db_name="geometry_learning.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # הפעלת תמיכה במפתחות זרים
    cursor.execute("PRAGMA foreign_keys = ON;")

    # יצירת טבלת המשולשים
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Triangles (
        triangle_id INTEGER PRIMARY KEY,
        triangle_type TEXT NOT NULL,
        active INTEGER DEFAULT 1
    )
    ''')

    # יצירת טבלת המשפטים הגיאומטריים
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Theorems (
        theorem_id INTEGER PRIMARY KEY AUTOINCREMENT,
        theorem_text TEXT NOT NULL,
        category INTEGER,
        active INTEGER DEFAULT 1,
        FOREIGN KEY (category) REFERENCES Triangles(triangle_id)
    )
    ''')

    # יצירת טבלת השאלות
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 3),
        active INTEGER DEFAULT 1
    )
    ''')


    # יצירת טבלת קשרים בין משולשים למשפטים כולל חוזק קשר#
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS TheoremTriangleMatrix (
        theorem_id INTEGER,
        triangle_id INTEGER,
        connection_strength FLOAT CHECK (connection_strength >= 0 AND connection_strength <= 1),
        PRIMARY KEY (theorem_id, triangle_id),
        FOREIGN KEY (theorem_id) REFERENCES Theorems(theorem_id),
        FOREIGN KEY (triangle_id) REFERENCES Triangles(triangle_id)
    )
    ''')

    # יצירת טבלת הקשרים בין משפטים לשאלות
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS TheoremQuestionMatrix (
        theorem_id INTEGER,
        question_id INTEGER,
        PRIMARY KEY (theorem_id, question_id),
        FOREIGN KEY (theorem_id) REFERENCES Theorems(theorem_id),
        FOREIGN KEY (question_id) REFERENCES Questions(question_id)
    )
    ''')

    # ✅ יצירת טבלת מקדמי התשובות (AnswerMultipliers)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS InitialAnswerMultipliers (
        question_id INTEGER,
        triangle_id INTEGER,
        answer_type TEXT NOT NULL,
        multiplier REAL NOT NULL,
        PRIMARY KEY (question_id, triangle_id, answer_type),
        FOREIGN KEY (question_id) REFERENCES Questions(question_id),
        FOREIGN KEY (triangle_id) REFERENCES Triangles(triangle_id)
    )
    ''')
    # ✅ יצירת טבלת תשובות במהלך השימוש (inputDuring)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inputDuring (
        ansID INTEGER PRIMARY KEY AUTOINCREMENT,
        ans TEXT NOT NULL
    )
    ''')

    # ✅ יצירת טבלת פידבק מהמשתמשים (inputFB)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inputFB (
        fbID INTEGER PRIMARY KEY AUTOINCREMENT,
        fb TEXT NOT NULL
    )
    ''')

    # ✅ יצירת טבלת תנאי קדימות בין שאלות
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS QuestionPrerequisites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prerequisite_question_id INTEGER,
        dependent_question_id INTEGER,
        FOREIGN KEY (prerequisite_question_id) REFERENCES Questions(question_id),
        FOREIGN KEY (dependent_question_id) REFERENCES Questions(question_id)
    )
    ''')





    conn.commit()
    conn.close()
    print("✅ Database and tables created successfully.")

# ✅ הוספת קריאה לפונקציה כדי שהיא תרוץ בפועל
if __name__ == "__main__":
    create_database()
