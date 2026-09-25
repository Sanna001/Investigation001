import json
import os
from typing import Dict, List, Any

class CaseLoader:
    def __init__(self, filepath: str = "cases.json"):
        # Якщо за першим шляхом немає, перевіряємо data/cases.json або відносні шляхи
        if not os.path.exists(filepath):
            possible_paths = [
                "data/cases.json",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases.json"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cases.json")
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    filepath = p
                    break

        self.filepath = filepath
        self._cases_cache = self._load_cases()

    def _load_cases(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            print(f"[ERROR] CaseLoader: Файл '{self.filepath}' не знайдено!")
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("cases", [])
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ERROR] CaseLoader помилка читання: {e}")
            return []

    def get_case_by_id(self, case_id: int) -> Dict[str, Any]:
        for c in self._cases_cache:
            if c.get("id") == case_id:
                return c
        raise ValueError(f"Справу з ID {case_id} не знайдено.")

    def get_starter_case(self, solved_count: int) -> Dict[str, Any]:
        """
        Повертає стартову справу (ID 404 / СПРАВА 001) з json-файлу для новачків.
        """
        if solved_count == 0:
            if self._cases_cache:
                return self._cases_cache[0]
            raise RuntimeError(f"Файл {self.filepath} порожній або не завантажився!")
        raise ValueError("Стартова справа доступна лише для гравців із 0 розв'язаних справ.")

    def get_cases_by_level(self, level: str) -> List[Dict[str, Any]]:
        return [c for c in self._cases_cache if c.get("level") == level]