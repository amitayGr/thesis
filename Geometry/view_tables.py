import sqlite3

# התחברות למסד הנתונים
conn = sqlite3.connect("geometry_learning.db")
cursor = conn.cursor()

# שליפת כל הטבלאות במסד הנתונים
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if not tables:
    print("❌ אין טבלאות במסד הנתונים!")
else:
    print("📌 רשימת הטבלאות במסד הנתונים:")
    for table in tables:
        print(f"➡️ {table[0]}")

    print("\n🔍 הצגת התוכן של כל טבלה:")

    # מעבר על כל הטבלאות והדפסת התוכן שלהן
    for table in tables:
        table_name = table[0]
        print(f"\n📜 תוכן טבלת {table_name}:")

        try:
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    print(row)
            else:
                print("⚠️ אין נתונים בטבלה.")

            print("=" * 50)
        except Exception as e:
            print(f"❌ שגיאה בעת שליפת נתונים מהטבלה {table_name}: {e}")

# סגירת החיבור
conn.close()
