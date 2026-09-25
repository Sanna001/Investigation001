import json
import os
from typing import Dict, List, Any

class CaseLoader:
    def __init__(self, filepath: str = "data/cases.json"):
        self.filepath = filepath
        self._cases_cache = self._load_cases()

    def _load_cases(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            return []
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("cases", [])

    def get_case_by_id(self, case_id: int) -> Dict[str, Any]:
        for c in self._cases_cache:
            if c["id"] == case_id:
                return c
        raise ValueError(f"Справу з ID {case_id} не знайдено.")

    def get_starter_case(self, solved_count: int) -> Dict[str, Any]:
        """
        Повертає стартову справу (ID 404) тільки якщо гравець не має розв'язаних справ.
        Якщо вже є розв'язані — викидає помилку, щоб система знала, що треба генерувати процедурну.
        """
        if solved_count == 0:
            return self.get_case_by_id(404)
        raise ValueError("Стартова справа доступна лише для новачків із нульовим досвідом.")

    def get_cases_by_level(self, level: str) -> List[Dict[str, Any]]:
        return [c for c in self._cases_cache if c.get("level") == level]