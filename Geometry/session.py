import json
import uuid
from typing import List

class Session:
    def __init__(self, session_id=None):
        self.session_id = session_id if session_id else str(uuid.uuid4())
        self.interactions = []  # רשימת מזהי השאלות והתשובות
        self.feedback = None  # משוב בסוף המסלול
        self.helpful_theorems = []  # מזהים של משפטים שסייעו למשתמש
        self.triangle_type = None # סוג המשולש שהיה בפועל כקלט מהמשתמש

    def add_interaction(self, question_id, answer_id):
        """מוסיף מזהה של שאלה ותשובה למסלול"""
        self.interactions.append({"question_id": question_id, "answer_id": answer_id})

    def set_feedback(self, feedback_id):
        """שומר את מזהה המשוב בסוף המסלול"""
        self.feedback = feedback_id

    def to_dict(self):
        """ממיר את המסלול למבנה JSON לשמירה"""
        return {
            "session_id": self.session_id,
            "interactions": self.interactions,
            "feedback": self.feedback,
            "triangle_type": self.triangle_type,
            "helpful_theorems": self.helpful_theorems
        }

    def to_json(self):
        """ממיר את המסלול למחרוזת JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)



    def set_helpful_theorems(self, theorem_ids):
        """שומר את רשימת המשפטים שסייעו למשתמש"""
        self.helpful_theorems = theorem_ids

    def set_triangle_type(self, triangle_ids: List[int]):
        """שומר את סוגי המשולשים שהמשתמש סימן כקשורים לתרגיל."""
        self.triangle_type = triangle_ids