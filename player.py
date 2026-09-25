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

    def load_profile(self, name: str) -> PlayerProfile:
        if not os.path.exists(self.filepath):
            return PlayerProfile(name=name)
        
        with open(self.filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if name in data:
                    p_data = data[name]
                    profile = PlayerProfile(
                        name=name,
                        password_hash=p_data.get("password_hash", ""),
                        solved_count=p_data.get("solved_count", 0),
                        total_score=p_data.get("total_score", 0),
                        current_level=p_data.get("current_level", "Junior Investigator")
                    )
                    profile.current_level = profile.get_rank()
                    return profile
            except json.JSONDecodeError:
                pass
        return PlayerProfile(name=name)

    def save_profile(self, profile: PlayerProfile):
        data = {}
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        profile.current_level = profile.get_rank()
        data[profile.name] = asdict(profile)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)