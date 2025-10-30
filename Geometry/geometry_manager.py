import sqlite3
from typing import List, Dict
import os
from session import Session
from session_db import SessionDB
from collections import defaultdict

class GeometryManager:
    def __init__(self, db_path="geometry_learning.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # מאפשר גישה נוחה לעמודות לפי שם
        self.state = self._initialize_state()
        self.session = Session()
        self.session_db = SessionDB()
        # ===== Back-to-exercise support =====
        self._pending_question = None  # תשמר כאן השאלה האחרונה שהוצגה למשתמש ועדיין ממתינה לתשובה
        self._resume_requested = False  # דגל: האם המשתמש ביקש "חזרה לתרגיל"

    def close(self):
        self.conn.close()

    def _initialize_state(self) -> Dict:
        """אתחול מצב פנימי - משקלים התחלתיים וכו'"""
        return {
            'triangle_weights': {
                0: 0.25,  # כללי
                1: 0.25,  # שווה צלעות
                2: 0.25,  # שווה שוקיים
                3: 0.25   # ישר זווית
            },
            'theorem_weights': self._initialize_theorem_weights(),
            'asked_questions': [],
            'questions_count': 0,
        }

    def _initialize_theorem_weights(self) -> Dict[int, float]:
        """Initialize all active theorems with minimal base weight."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT theorem_id FROM Theorems WHERE active = 1")
        return {theorem[0]: 0.01 for theorem in cursor.fetchall()}

    def get_first_question(self) -> Dict:
        """בחר שאלה ראשונה מתוך שאלות קלות ועדכן את ההיסטוריה."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT question_id, question_text 
            FROM Questions 
            WHERE active = 1 AND difficulty_level = 1
        """)
        easy_questions = cursor.fetchall()

        if not easy_questions:
            return {"error": "No easy questions found."}

        import random
        selected = random.choice(easy_questions)
        question_id, question_text = selected["question_id"], selected["question_text"]

        self.state['asked_questions'].append(question_id)
        self.state['questions_count'] += 1

        return {
            "question_id": question_id,
            "question_text": question_text
        }

    def get_questions_history(self) -> dict:
        """
        מחזירה את ההיסטוריה של השאלות שנשאלו ואת מספרן הנוכחי.
        """
        state = self.state
        return {
            'asked_questions': state['asked_questions'],
            'questions_count': state['questions_count']
        }

    def _store_pending_question(self, question_obj: Dict):
        """שומר את השאלה המוצגת כרגע (לפני קבלת תשובה) כדי שנוכל לחזור אליה."""
        self._pending_question = question_obj

    def _pop_pending_question(self) -> Dict:
        """מחזיר את השאלה הממתינה ומנקה אותה (כשמסיימים לענות עליה)."""
        q = self._pending_question
        self._pending_question = None
        return q

    ##בדיקה
    def print_state(self):
        print("📊 מצב פנימי נוכחי:")
        print(self.state)

    def _calculate_entropy(self, probabilities: List[float]) -> float:
        """חישוב אנטרופיה לפי התפלגות הסתברויות."""
        import math
        return -sum(p * math.log2(p) for p in probabilities if p > 0)

    def _calculate_question_relevance_score(self, question_id: int, triangle_weights: Dict[int, float]) -> float:
        """
        מחשבת עד כמה השאלה רלוונטית לפי המשקלים הנוכחיים של סוגי המשולשים,
        תוך שימוש במכפילים דינאמיים אם קיימים, אחרת בבייסליין.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT triangle_id, answer_id, COALESCE(dynamic_multiplier, baseline_multiplier) AS multiplier
            FROM DynamicAnswerMultipliers
            WHERE question_id = ?
        """, (question_id,))

        max_impact = 0
        active_triangles = {tid for tid, weight in triangle_weights.items() if weight > 0.05}

        for row in cursor.fetchall():
            triangle_id = row["triangle_id"]
            multiplier = row["multiplier"]

            if triangle_id in active_triangles:
                current_weight = triangle_weights[triangle_id]
                potential_change = abs(current_weight * multiplier - current_weight)
                max_impact = max(max_impact, potential_change)

        return max_impact

    def _calculate_information_gain(self, question_id: int) -> float:
        """
        מחשב רווח מידע של שאלה לפי שינוי באנטרופיה,
        תוך שימוש במכפילים דינאמיים אם קיימים, אחרת בבייסליין.
        """
        current_weights = self.state['triangle_weights']
        current_entropy = self._calculate_entropy(list(current_weights.values()))

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT triangle_id, answer_id, COALESCE(dynamic_multiplier, baseline_multiplier) AS multiplier
            FROM DynamicAnswerMultipliers
            WHERE question_id = ?
        """, (question_id,))

        # ארגון לפי תשובה מספרית
        answer_groups = {}
        for triangle_id, answer_id, multiplier in cursor.fetchall():
            if answer_id not in answer_groups:
                answer_groups[answer_id] = []
            answer_groups[answer_id].append((triangle_id, multiplier))

        expected_entropy = 0
        total_weight = 0

        for answer_id, multipliers in answer_groups.items():
            simulated_weights = current_weights.copy()

            for triangle_id, multiplier in multipliers:
                simulated_weights[triangle_id] *= multiplier

            # נרמול
            total = sum(simulated_weights.values())
            if total > 0:
                for tid in simulated_weights:
                    simulated_weights[tid] /= total

            entropy = self._calculate_entropy(list(simulated_weights.values()))

            # הערכת הסתברות לקבלת תשובה זו לפי משקלי המשולשים
            prob = sum(current_weights[tid] * mult for tid, mult in multipliers)
            expected_entropy += prob * entropy
            total_weight += prob

        if total_weight > 0:
            expected_entropy /= total_weight
            return current_entropy - expected_entropy

        return 0


##מקורית
    # def get_next_question(self) -> dict:
    #     """
    #     בוחרת את השאלה הבאה בהתבסס על משקלי המשולשים, רווח מידע ורלוונטיות.
    #     """
    #     cursor = self.conn.cursor()
    #     state = self.state
    #
    #     # שלב א: אם לא נשאלה אף שאלה – בחר שאלה קלה באקראי
    #     if len(state['asked_questions']) == 0:
    #         cursor.execute("""
    #             SELECT question_id, question_text
    #             FROM Questions
    #             WHERE difficulty_level = 1 AND active = 1
    #         """)
    #         easy_questions = cursor.fetchall()
    #         if not easy_questions:
    #             return {"error": "No easy questions found."}
    #
    #         import random
    #         selected = random.choice(easy_questions)
    #         question_id, question_text = selected[0], selected[1]
    #
    #         # עדכון מצב פנימי
    #         state['asked_questions'].append(question_id)
    #         state['questions_count'] += 1
    #
    #         return {
    #             "question_id": question_id,
    #             "question_text": question_text,
    #             "info": "שאלה ראשונה נבחרה באקראי"
    #         }
    #
    #     # שלב ב: שליפת כל השאלות הפעילות
    #     cursor.execute("""
    #         SELECT question_id, question_text
    #         FROM Questions
    #         WHERE active = 1
    #     """)
    #     all_questions = cursor.fetchall()
    #
    #     # שלב ג: חישוב ציון לכל שאלה (רלוונטיות * רווח מידע)
    #     scores = {}
    #     triangle_weights = state['triangle_weights']
    #     asked_ids = set(state['asked_questions'])
    #
    #     for qid, qtext in all_questions:
    #         if qid in asked_ids:
    #             continue  # דלג על שאלות שכבר נשאלו
    #
    #         relevance = self._calculate_question_relevance_score(qid, triangle_weights)
    #         info_gain = self._calculate_information_gain(qid)
    #
    #         score = relevance * info_gain
    #         if score > 0:
    #             scores[qid] = (score, qtext)
    #
    #     # שלב ד: בחירה בשאלה עם הציון הגבוה ביותר
    #     if not scores:
    #         return {"error": "לא נמצאה שאלה מתאימה עם רלוונטיות ורווח מידע חיוביים."}
    #
    #     best_qid = max(scores, key=lambda k: scores[k][0])
    #     best_text = scores[best_qid][1]
    #
    #     # עדכון מצב פנימי
    #     state['asked_questions'].append(best_qid)
    #     state['questions_count'] += 1
    #
    #     return {
    #         "question_id": best_qid,
    #         "question_text": best_text,
    #         "info": "שאלה נבחרה לפי חישוב משולב של רלוונטיות ורווח מידע"
    #     }

##עדכני - בודק שכל שאלה שנשאלת עומדת בתנאי קדימות

    def get_next_question(self) -> dict:
        """
        בוחרת את השאלה הבאה בהתבסס על משקלי המשולשים, רווח מידע ורלוונטיות,
        תוך כיבוד אילוצי הקדימויות מתוך טבלת QuestionPrerequisites.
        """
        cursor = self.conn.cursor()
        state = self.state

        # שלב א: אם לא נשאלה אף שאלה – בחר שאלה קלה באקראי
        if len(state['asked_questions']) == 0:
            cursor.execute("""
                SELECT question_id, question_text
                FROM Questions
                WHERE difficulty_level = 1 AND active = 1
            """)
            easy_questions = cursor.fetchall()

            if not easy_questions:
                return {"error": "No easy questions found."}

            import random
            selected = random.choice(easy_questions)
            question_id, question_text = selected

            # עדכון מצב פנימי
            state['asked_questions'].append(question_id)
            state['questions_count'] += 1

            return {
                "question_id": question_id,
                "question_text": question_text,
                "info": "שאלה ראשונה נבחרה באקראי"
            }

        # שלב ב: שליפת כל השאלות הפעילות
        cursor.execute("""
            SELECT question_id, question_text
            FROM Questions
            WHERE active = 1
        """)
        all_questions = cursor.fetchall()

        # שלב ג: שליפת אילוצי קדימות
        cursor.execute("""
            SELECT prerequisite_question_id, dependent_question_id
            FROM QuestionPrerequisites
        """)
        prerequisites = cursor.fetchall()
        prerequisite_map = {}
        for prereq_id, dep_id in prerequisites:
            prerequisite_map.setdefault(dep_id, set()).add(prereq_id)

        # שלב ד: חישוב ציונים רק לשאלות שאינן נשאלו ושאין להן תנאי קדימות פתוחים
        scores = {}
        triangle_weights = state['triangle_weights']
        asked_ids = set(state['asked_questions'])

        for qid, qtext in all_questions:
            if qid in asked_ids:
                continue

            # בדיקת תנאי קדימות (אם קיימים)
            required = prerequisite_map.get(qid, set())
            if not required.issubset(asked_ids):
                continue  # יש תנאי קדימות שעדיין לא התקיימו

            relevance = self._calculate_question_relevance_score(qid, triangle_weights)
            info_gain = self._calculate_information_gain(qid)

            score = relevance * info_gain
            if score > 0:
                scores[qid] = (score, qtext)

        # שלב ה: בחירה בשאלה עם הציון הגבוה ביותר
        if not scores:
            return {"error": "לא נמצאה שאלה מתאימה שעומדת בתנאי הקדימות וברלוונטיות."}

        best_qid = max(scores, key=lambda k: scores[k][0])
        best_text = scores[best_qid][1]

        # עדכון מצב פנימי
        state['asked_questions'].append(best_qid)
        state['questions_count'] += 1

        return {
            "question_id": best_qid,
            "question_text": best_text,
            "info": "שאלה נבחרה לפי חישוב משולב של רלוונטיות, רווח מידע ותנאי קדימות"
        }

    def process_answer(self, question_id: int, answer_id: int):
        """
        מעבד תשובה של המשתמש לשאלה מסוימת ומעדכן את משקלי המשולשים והמשפטים.
        מדפיס את המשפטים הרלוונטיים לאחר עדכון.
        """
        self._update_triangle_weights(question_id, answer_id)
        self._update_theorem_weights()
        self.session.add_interaction(question_id, answer_id)

        # ✅ הדפסת משקלי המשולשים
        print("\n📐 משקלי המשולשים לאחר העדכון:")
        triangle_names = {0: "כללי", 1: "שווה צלעות", 2: "שווה שוקיים", 3: "ישר זווית"}
        for tid, weight in self.state['triangle_weights'].items():
            print(f"🔸 {triangle_names.get(tid, 'לא ידוע')} ({tid}): {weight:.3f}")

        # ✅ הדפסת המשפטים הרלוונטיים
        relevant_theorems = self.get_relevant_theorems(question_id, answer_id)
        print("\n📌 משפטים רלוונטיים לאחר העדכון:")
        triangle_types = {0: "כללי", 1: "שווה צלעות", 2: "שווה שוקיים", 3: "ישר זווית"}
        for th in relevant_theorems:
            category_name = triangle_types.get(th["category"], "לא ידוע")
            print(
                f"🔹 [{th['theorem_id']}] {th['theorem_text']} (סוג: {category_name}, ציון: {th['combined_score']:.3f})")

        # ✅ חשוב: אחרי שעיבדנו תשובה, מנקים את השאלה הממתינה
        self._pop_pending_question()

        ##המקורית
    # def get_relevant_theorems(self, base_threshold: float = 0.01) -> List[Dict]:
    #     """
    #     מחזירה את רשימת המשפטים הרלוונטיים לפי משקלי המשפטים.
    #     אם זו השאלה הראשונה – מחזירה את כל המשפטים הפעילים עם משקל בסיסי.
    #     אחרת – רק את אלה שמשקלם מעל סף סינון שמתעדכן לפי מספר השאלות שנשאלו.
    #     """
    #     state = self.state
    #     num_questions = state['questions_count']
    #     cursor = self.conn.cursor()
    #
    #     # שלב 1: אם זו השאלה הראשונה – מחזירים את כל המשפטים הפעילים עם משקל בסיסי
    #     if num_questions == 1:
    #         cursor.execute("SELECT theorem_id, theorem_text, category FROM Theorems WHERE active = 1")
    #         all_theorems = cursor.fetchall()
    #         return [
    #             {"theorem_id": row["theorem_id"], "theorem_text": row["theorem_text"], "weight": 0.01, "category": row["category"]}
    #             for row in all_theorems
    #         ]
    #
    #     # שלב 2: קביעת סף סינון דינאמי
    #     increment_factor = 0.05
    #     threshold = base_threshold + (num_questions * increment_factor)
    #
    #     # שלב 3: מיון המשפטים הרלוונטיים לפי משקל
    #     result = []
    #     for theorem_id, weight in state['theorem_weights'].items():
    #         if weight >= threshold:
    #             cursor.execute("""
    #                 SELECT theorem_text, category
    #                 FROM Theorems
    #                 WHERE theorem_id = ?
    #             """, (theorem_id,))
    #             row = cursor.fetchone()
    #             if row:
    #                 result.append({
    #                     "theorem_id": theorem_id,
    #                     "theorem_text": row["theorem_text"],
    #                     "weight": weight,
    #                     "category": row["category"]
    #                 })
    #
    #     # שלב 4: מיון לפי משקל מהגבוה לנמוך
    #     return sorted(result, key=lambda x: x["weight"], reverse=True)

##שליפת המשפטים הרלוונטיים ללא סדר לפי האלגוריתם המקורי של קארין ואפיק
    def _get_list_of_relevant_theorems(self, base_threshold: float = 0.01) -> List[Dict]:
        """
        מחזירה את רשימת המשפטים הרלוונטיים לפי משקלי המשפטים בלבד,
        בלי למיין אותם. תשתמש בה get_relevant_theorems() כדי למיין בהמשך.
        """
        state = self.state
        num_questions = state['questions_count']
        cursor = self.conn.cursor()

        # שלב 1: אם זו השאלה הראשונה – מחזירים את כל המשפטים הפעילים עם משקל בסיסי
        if num_questions == 1:
            cursor.execute("SELECT theorem_id, theorem_text, category FROM Theorems WHERE active = 1")
            all_theorems = cursor.fetchall()
            return [
                {
                    "theorem_id": row["theorem_id"],
                    "theorem_text": row["theorem_text"],
                    "weight": 0.01,
                    "category": row["category"]
                }
                for row in all_theorems
            ]

        # שלב 2: קביעת סף סינון דינאמי
        increment_factor = 0.05
        threshold = base_threshold + (num_questions * increment_factor)

        # שלב 3: שליפת משפטים שמשקלם מעל הסף
        result = []
        for theorem_id, weight in state['theorem_weights'].items():
            if weight >= threshold:
                cursor.execute("""
                    SELECT theorem_text, category 
                    FROM Theorems 
                    WHERE theorem_id = ?
                """, (theorem_id,))
                row = cursor.fetchone()
                if row:
                    result.append({
                        "theorem_id": theorem_id,
                        "theorem_text": row["theorem_text"],
                        "weight": weight,
                        "category": row["category"]
                    })

        return result





    ## לצורך הצגת המשפטים עם דירוג חכם - חישוב משקל המשולש בהתאם למצב בסשן
    def get_triangle_score(self, theorem_id: int) -> float:
        """
        מחשבת את ציון ההתאמה בין משפט לבין התפלגות המשולשים הנוכחית,
        לפי עוצמות קשר בטבלת TheoremTriangleMatrix.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT triangle_id, connection_strength
            FROM TheoremTriangleMatrix
            WHERE theorem_id = ?
        """, (theorem_id,))
        rows = cursor.fetchall()

        triangle_weights = self.state['triangle_weights']
        score = 0.0

        for row in rows:
            triangle_id = row["triangle_id"]
            strength = row["connection_strength"]
            weight = triangle_weights.get(triangle_id, 0)
            score += strength * weight

        return score
##לצורך הצגת המשפטים בדירוג חכם - שליפת ערך ה SCORE של המשפט בשילוב עם השאלה והתשובה
    def get_theorem_score(self, question_id: int, answer_id: int, theorem_id: int) -> float:
        """
        מחזירה את ערך score מטבלת TheoremScores עבור שאלה, תשובה ומשפט נתונים.
        הנחה: כל הצירופים קיימים בטבלה.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT score
            FROM TheoremScores
            WHERE question_id = ? AND answer_id = ? AND theorem_id = ?
        """, (question_id, answer_id, theorem_id))
        row = cursor.fetchone()
        return row["score"]
##לצורך הצגת המשפטים בדירוג חכם - שליפת ערך התרומה הכללית של המשפט
    def get_general_helpfulness(self, theorem_id: int) -> float:
        """
        מחזירה את ערך general_helpfulness של משפט מסוים מתוך הטבלה TheoremGeneralHelpfulness.
        הנחה: כל המשפטים קיימים בטבלה (1–63), ולכן אין צורך בערך ברירת מחדל.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT general_helpfulness
            FROM TheoremGeneralHelpfulness
            WHERE theorem_id = ?
        """, (theorem_id,))
        row = cursor.fetchone()
        return row["general_helpfulness"]
#מיון המשפטים שהתקבלו בסדר חכם
    def _sort_theorems_by_combined_score(self, theorems: List[Dict], question_id: int, answer_id: int) -> List[Dict]:
        """
        מקבלת רשימת משפטים (כפי שחוזרת מ־_get_list_of_relevant_theorems) ומחזירה אותם ממוינים
        לפי שקלול משוקלל של:
        - התאמה למשולשים (triangle score)
        - score לפי שאלה-תשובה-משפט
        - general_helpfulness
        """
        # 🧮 הגדרת המשקולות (מודולרי)
        W1 = 0.7  # משקל להתאמה למשולשים
        W2 = 0.2  # משקל ל־score מתוך TheoremScores
        W3 = 0.1  # משקל ל־general_helpfulness מתוך TheoremGeneralHelpfulness

        scored_theorems = []

        for th in theorems:
            tid = th["theorem_id"]

            triangle_score = self.get_triangle_score(tid)
            theorem_score = self.get_theorem_score(question_id, answer_id, tid)
            general_helpfulness = self.get_general_helpfulness(tid)

            combined_score = (
                    W1 * triangle_score +
                    W2 * theorem_score +
                    W3 * general_helpfulness
            )

            th_with_score = th.copy()
            th_with_score["combined_score"] = combined_score

            scored_theorems.append(th_with_score)

        # מיון לפי הציון המשוקלל מהגבוה לנמוך
        return sorted(scored_theorems, key=lambda x: x["combined_score"], reverse=True)



    ##החדשה
    def get_relevant_theorems(self, question_id: int, answer_id: int, base_threshold: float = 0.01) -> List[Dict]:
        """
        מחזירה את רשימת המשפטים הרלוונטיים, ממוינת לפי ציון משוקלל שמבוסס על:
        - התאמה למשולשים (triangle score)
        - score לפי שאלה-תשובה-משפט
        - general_helpfulness

        נדרשים question_id ו־answer_id לצורך חישוב הציון.
        """
        theorems = self._get_list_of_relevant_theorems(base_threshold=base_threshold)
        sorted_theorems = self._sort_theorems_by_combined_score(theorems, question_id, answer_id)
        return sorted_theorems

    def _update_triangle_weights(self, question_id: int, answer_id: int):
        """
        עדכון משקלי המשולשים לפי התשובה שהתקבלה,
        תוך שימוש במכפילים דינאמיים אם קיימים, אחרת בבייסליין.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT triangle_id,
                   COALESCE(dynamic_multiplier, baseline_multiplier) AS multiplier
            FROM DynamicAnswerMultipliers
            WHERE question_id = ? AND answer_id = ?
        """, (question_id, answer_id))

        multipliers = cursor.fetchall()
        if not multipliers:
            print(f"⚠️ לא נמצאו מכפילים לשאלה {question_id} ולתשובה {answer_id}")
            return

        current_weights = self.state['triangle_weights']
        new_weights = current_weights.copy()

        for triangle_id, multiplier in multipliers:
            new_weights[triangle_id] *= multiplier

        # נרמול המשקלים כך שסכומם יהיה 1
        total = sum(new_weights.values())
        if total > 0:
            for tid in new_weights:
                new_weights[tid] /= total

        self.state['triangle_weights'] = new_weights

    def _update_theorem_weights(self):
        """
        עדכון משקלי המשפטים לפי משקלי המשולשים, לפי טבלת TheoremTriangleMatrix.
        """
        cursor = self.conn.cursor()
        triangle_weights = self.state['triangle_weights']

        cursor.execute("""
            SELECT theorem_id, triangle_id, connection_strength 
            FROM TheoremTriangleMatrix
        """)
        rows = cursor.fetchall()

        new_weights = {}

        for row in rows:
            theorem_id = row['theorem_id']
            triangle_id = row['triangle_id']
            strength = row['connection_strength']

            if strength < 0.9:
                continue  # מתעלמים מחיבורים חלשים

            weight = triangle_weights.get(triangle_id, 0) * strength

            if theorem_id not in new_weights:
                new_weights[theorem_id] = 0

            new_weights[theorem_id] += weight

        self.state['theorem_weights'] = new_weights


## קבלת פידבק מהמשתמש
    def _collect_feedback(self) -> int:
        print("\n📌 בחר את הפידבק שלך:")
        print("(4) לא הצלחתי הפעם")
        print("(5) הצלחתי תודה")
        print("(6) התקדמתי אבל אנסה תרגיל חדש")
        print("(7) חזרה לתרגיל")

        valid_feedback = {"4", "5", "6", "7"}
        feedback = input("👉 אנא הזן את מספר הפידבק: ").strip()

        while feedback not in valid_feedback:
            print("⚠️ בחירה לא תקפה, נסה שנית.")
            feedback = input("👉 אנא הזן את מספר הפידבק: ").strip()

        # ✅ לא שומרים ב־Session כאן, רק מחזירים את הערך
        return int(feedback)

        ##קבלת סוג המשולש שהיה בפועל בתרגיל

    def _collect_triangle_types(self):
        print("\n🔺 איזה סוג או סוגי משולשים היו רלוונטיים לתרגיל?")
        print("0: כללי, 1: שווה צלעות, 2: שווה שוקיים, 3: ישר זווית")
        print("📭 אם אינך רוצה להזין - הקלד @ ולחץ אנטר")

        while True:
            raw_input = input("👉 סוגי משולשים: ").strip()

            if raw_input == "@":
                return  # המשתמש לא רוצה להזין

            try:
                triangle_ids = [int(x) for x in raw_input.split() if x.isdigit()]
                valid_ids = [tid for tid in triangle_ids if tid in [0, 1, 2, 3]]

                if not triangle_ids:
                    print("⚠️ לא הוזן אף מספר. נסה שוב או הקלד '@' לדילוג.")
                    continue

                if len(valid_ids) < len(triangle_ids):
                    print("⚠️ הוזנו מספרים לא תקינים. רק הערכים 0, 1, 2, 3 מותרים.")
                    continue

                self.session.set_triangle_type(valid_ids)
                break

            except ValueError:
                print("⚠️ קלט לא תקין. נסה שוב.")

    ##קבלת המשפטים שהיו נחוצים למשתמש
    def _collect_helpful_theorems(self):
        print("\n🧠 אילו משפטים סייעו או היו מסייעים לך בפתרון השאלות?")
        print("🔢 תוכל להזין מספרי משפטים מופרדים ברווח (למשל: 2 3 5 47)")
        print("📭 אם אינך רוצה להזין - הקלד 0 ולחץ אנטר")

        raw_input = input("👉 משפטים: ").strip()

        if raw_input != "0":
            try:
                theorem_ids = [int(x) for x in raw_input.split() if x.isdigit()]
                valid_ids = [tid for tid in theorem_ids if 1 <= tid <= 63]

                if valid_ids:
                    self.session.set_helpful_theorems(valid_ids)
                else:
                    print("⚠️ אף מספר לא היה בטווח התקין (1–63), לא נשמרו משפטים.")
            except ValueError:
                print("⚠️ קלט לא תקין, לא נשמרו משפטים.")
    ## סיום סשן וקבלת פידבקים
    def handle_session_end(self):
        fb = self._collect_feedback()

        # ✅ אם המשתמש ביקש חזרה לתרגיל – לא שומרים סשן ולא מבקשים עוד מידע
        if fb == 7:
            self._resume_requested = True
            print("🔁 בחרת חזרה לתרגיל — נשוב לאותה שאלה.")
            return "resume"

        # ✅ אחרת: שומרים את הפידבק וממשיכים לשלב איסוף נתונים ושמירה
        self.session.set_feedback(fb)
        self._collect_triangle_types()
        self._collect_helpful_theorems()

        # שמירת הסשן במסד הנתונים
        self.session_db.save_session(self.session)
        print("\n✅ תודה על המשוב! הסשן נשמר בהצלחה.")
        print("\n📄 סשן שנשמר:")
        print(self.session.to_json())

        return "saved"

# if __name__ == "__main__":
#     # gm = GeometryManager()
#     # q = gm.get_next_question()
#     # print("🔹 שאלה שנבחרה:", q)
#     #
#     # # בדיקת עיבוד תשובה
#     # gm.process_answer(q['question_id'], answer='yes')  # או 'no', תלוי בתשובות שיש
#     # gm.print_state()
#     #
#     # gm.close()
#
#     gm = GeometryManager()
#
#     print("📌 DB file path:", os.path.abspath(gm.db_path))
#
#     # הדפסת שמות הטבלאות במסד הנתונים
#     cursor = gm.conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
#     tables = cursor.fetchall()
#
#     print("📋 Tables in DB:")
#     for t in tables:
#         print("-", t[0])


## מיין בדיקה





if __name__ == "__main__":
    gm = GeometryManager()
    print("📌 DB file path:", os.path.abspath(gm.db_path))

    while True:
        # 1) אם ביקשו חזרה לתרגיל ויש לנו שאלה ממתינה — נשתמש בה
        if gm._resume_requested and gm._pending_question:
            q = gm._pending_question
            gm._resume_requested = False
            print("\n🔁 חזרה לאותה שאלה:")
        else:
            # 2) אחרת נבקש שאלה חדשה ונשמור אותה כשאלה ממתינה
            q = gm.get_next_question()
            gm._store_pending_question(q)
        if "error" in q:
            print("⚠️", q["error"])
            break

        print("\n🔹 שאלה שנבחרה:")
        print(q['question_text'])

        # שליפת אפשרויות תשובה
        cursor = gm.conn.cursor()
        cursor.execute("SELECT ansID, ans FROM inputDuring")
        answers = cursor.fetchall()

        print("\n💬 אפשרויות תשובה:")
        for ans in answers:
            print(f"{ans['ansID']}: {ans['ans']}")

        user_input = input("👉 בחר מספר תשובה (או '#' לסיום ולקבלת פידבק): ")

        if user_input == "#":
            action = gm.handle_session_end()
            if action == "resume":
                # לא מסיימים, לא שומרים — ממשיכים לאותה שאלה באיטרציה הבאה
                print("🎯 חוזרים לאותה שאלה.")
                continue
            else:
                break  # סיום רגיל של הסשן

        if user_input not in [str(ans['ansID']) for ans in answers]:
            print("⚠️ תשובה לא חוקית. נסה שוב.")
            continue

        answer_id = int(user_input)
        gm.process_answer(q['question_id'], answer_id)

        print("✅ תשובה עובדה ונשמרה בסשן.")

        print("\n📄 סשן נוכחי:")
        print(gm.session.to_json())
        print("\n" + "="*60 + "\n")

    gm.close()