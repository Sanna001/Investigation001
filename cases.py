import json
import os
from typing import Dict, List, Any

# Резервна СПРАВА 001 на випадок, якщо файл на сервері взагалі відсутній
HARDCODED_STARTER_CASE = {
    "id": 404,
    "title": "СПРАВА 001: НІЧНИЙ ІНЦИДЕНТ У СЕРВЕРНІЙ",
    "mode": "Доведення",
    "level": "Junior Investigator",
    "description": "О 03:00 ночі в головному дата-центрі спрацювала сирена. У цей час там перебували співробітники: системний адміністратор Віктор, нічний черговий Андрій та стажер Богдан. Віктор стверджує, що міцно спав і нічого не чув. Проаналізувавши свідчення та логи безпеки, доведіть за допомогою логіки, чи справді Віктор спав.",
    "legend": {
        "A": "Андрій був у серверній о 03:00",
        "B": "Богдан відкривав двері службовим ключем о 03:01",
        "S": "Сигналізація в дата-центрі була активована",
        "V": "Віктор спав на своєму робочому місці"
    },
    "axioms": [
        "(A v B)",
        "(B -> S)",
        "(S -> ~V)",
        "~A"
    ],
    "target_hypothesis": "~V"
}

class CaseLoader:
    def __init__(self, filename: str = "cases.json"):
        # Визначаємо абсолютний шлях до кореневої папки проєкту відносно цього файлу cases.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            os.path.join(base_dir, filename),
            os.path.join(base_dir, "data", filename),
            os.path.join(os.getcwd(), filename),
            os.path.join(os.getcwd(), "data", filename),
            filename
        ]
        
        self.filepath = None
        for path in possible_paths:
            if os.path.exists(path):
                self.filepath = path
                break

        self._cases_cache = self._load_cases()

    def _load_cases(self) -> List[Dict[str, Any]]:
        if not self.filepath or not os.path.exists(self.filepath):
            print("[WARNING] CaseLoader: Файл cases.json не знайдено на диску! Використовуємо резервну СПРАВУ 001.")
            return [HARDCODED_STARTER_CASE]
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                cases = data.get("cases", [])
                return cases if cases else [HARDCODED_STARTER_CASE]
        except Exception as e:
            print(f"[ERROR] CaseLoader помилка читання JSON: {e}")
            return [HARDCODED_STARTER_CASE]

    def get_case_by_id(self, case_id: int) -> Dict[str, Any]:
        for c in self._cases_cache:
            if c.get("id") == case_id:
                return c
        return HARDCODED_STARTER_CASE

    def get_starter_case(self, solved_count: int) -> Dict[str, Any]:
        """
        Повертає стартову справу (СПРАВА 001) для новачків.
        """
        if solved_count == 0:
            if self._cases_cache:
                return self._cases_cache[0]
            return HARDCODED_STARTER_CASE
        raise ValueError("Стартова справа доступна лише для гравців із 0 розв'язаних справ.")

    def get_cases_by_level(self, level: str) -> List[Dict[str, Any]]:
        return [c for c in self._cases_cache if c.get("level") == level]