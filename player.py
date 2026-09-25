import json
import os
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class PlayerProfile:
    def __init__(self, name: str, password_hash: str = "", solved_count: int = 0, total_score: int = 0, current_level: str = "Junior Investigator"):
        self.name = name
        self.password_hash = password_hash
        self.solved_count = solved_count
        self.total_score = total_score
        self.current_level = current_level

    def get_rank(self) -> str:
        if self.total_score >= 100:
            return "Senior Investigator"
        elif self.total_score >= 40:
            return "Middle Investigator"
        return "Junior Investigator"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "password_hash": self.password_hash,
            "solved_count": self.solved_count,
            "total_score": self.total_score,
            "current_level": self.current_level
        }

class PlayerManager:
    def __init__(self, filename: str = "players.json"):
        # Абсолютний шлях до папки, де лежить player.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Перевіряємо можливі розташування
        possible_paths = [
            os.path.join(base_dir, filename),
            os.path.join(base_dir, "data", filename),
            os.path.join(os.getcwd(), filename),
            os.path.join(os.getcwd(), "data", filename)
        ]
        
        self.filepath = possible_paths[0]
        for p in possible_paths:
            if os.path.exists(p):
                self.filepath = p
                break

        self.players = self._load_all()

    def _load_all(self) -> dict:
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Помилка зчитування {self.filepath}: {e}")
            return {}

    def exists(self, username: str) -> bool:
        return any(u.lower() == username.lower() for u in self.players.keys())

    def get_real_name(self, username: str) -> str:
        for u in self.players.keys():
            if u.lower() == username.lower():
                return u
        return username

    def load_profile(self, username: str) -> PlayerProfile:
        real_name = self.get_real_name(username)
        data = self.players.get(real_name)
        if data:
            return PlayerProfile(
                name=data.get("name", real_name),
                password_hash=data.get("password_hash", ""),
                solved_count=data.get("solved_count", 0),
                total_score=data.get("total_score", 0),
                current_level=data.get("current_level", "Junior Investigator")
            )
        return PlayerProfile(name=username)

    def save_profile(self, profile: PlayerProfile):
        # Оновлюємо внутрішній словник
        self.players[profile.name] = profile.to_dict()
        
        # Записуємо з примусовим скиданням буфера на диск (flush + os.fsync)
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.players, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
            print(f"[SUCCESS] Профіль {profile.name} успішно збережено у {self.filepath}")
        except Exception as e:
            print(f"[ERROR] Не вдалося зберегти {self.filepath}: {e}")