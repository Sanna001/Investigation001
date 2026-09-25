import json
import os
import hashlib
from dataclasses import dataclass, asdict

@dataclass
class PlayerProfile:
    name: str
    password_hash: str = ""
    solved_count: int = 0
    total_score: int = 0
    current_level: str = "Junior Investigator"

    def get_rank(self) -> str:
        if self.solved_count >= 10:
            return "Senior Investigator"
        elif self.solved_count >= 5:
            return "Middle Investigator"
        else:
            return "Junior Investigator"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class PlayerManager:
    def __init__(self, filepath: str = "data/players.json"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def _read_all(self) -> dict:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def exists(self, name: str) -> bool:
        """Перевіряє, чи існує гравець із таким ім'ям (без урахування регістру)."""
        data = self._read_all()
        target = name.strip().lower()
        return any(k.lower() == target for k in data.keys())

    def get_real_name(self, name: str) -> str:
        """Повертає канонічне ім'я з бази (з правильним регістром)."""
        data = self._read_all()
        target = name.strip().lower()
        for k in data.keys():
            if k.lower() == target:
                return k
        return name.strip()

    def load_profile(self, name: str) -> PlayerProfile:
        """Завантажує профіль або повертає новий порожній."""
        data = self._read_all()
        real_name = self.get_real_name(name)
        
        if real_name in data:
            p_data = data[real_name]
            profile = PlayerProfile(
                name=real_name,
                password_hash=p_data.get("password_hash", ""),
                solved_count=p_data.get("solved_count", 0),
                total_score=p_data.get("total_score", 0),
                current_level=p_data.get("current_level", "Junior Investigator")
            )
            profile.current_level = profile.get_rank()
            return profile
            
        return PlayerProfile(name=name.strip())

    def save_profile(self, profile: PlayerProfile):
        """Зберігає/оновлює профіль у JSON-файлі."""
        data = self._read_all()
        profile.current_level = profile.get_rank()
        data[profile.name] = asdict(profile)
        
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)