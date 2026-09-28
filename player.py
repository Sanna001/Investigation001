import hashlib
from database import SessionLocal, PlayerModel

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
    def exists(self, username: str) -> bool:
        db = SessionLocal()
        try:
            player = db.query(PlayerModel).filter(PlayerModel.username.ilike(username)).first()
            return player is not None
        finally:
            db.close()

    def get_real_name(self, username: str) -> str:
        db = SessionLocal()
        try:
            player = db.query(PlayerModel).filter(PlayerModel.username.ilike(username)).first()
            if player:
                return player.name
            return username
        finally:
            db.close()

    def load_profile(self, username: str) -> PlayerProfile:
        db = SessionLocal()
        try:
            player = db.query(PlayerModel).filter(PlayerModel.username.ilike(username)).first()
            if player:
                return PlayerProfile(
                    name=player.name,
                    password_hash=player.password_hash,
                    solved_count=player.solved_count,
                    total_score=player.total_score,
                    current_level=player.current_level
                )
            return PlayerProfile(name=username)
        finally:
            db.close()

    def save_profile(self, profile: PlayerProfile):
        db = SessionLocal()
        try:
            player = db.query(PlayerModel).filter(PlayerModel.username.ilike(profile.name)).first()
            if not player:
                player = PlayerModel(
                    username=profile.name.lower(),
                    name=profile.name,
                    password_hash=profile.password_hash,
                    solved_count=profile.solved_count,
                    total_score=profile.total_score,
                    current_level=profile.current_level
                )
                db.add(player)
            else:
                player.name = profile.name
                player.password_hash = profile.password_hash
                player.solved_count = profile.solved_count
                player.total_score = profile.total_score
                player.current_level = profile.current_level

            db.commit()
            print(f"[SUCCESS] Профіль {profile.name} успішно збережено у БД.")
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Помилка збереження профілю {profile.name} у БД: {e}")
        finally:
            db.close()

    def get_all_players(self):
        """Отримує список усіх гравців із бази даних."""
        db = SessionLocal()
        try:
            return db.query(PlayerModel).all()
        finally:
            db.close()