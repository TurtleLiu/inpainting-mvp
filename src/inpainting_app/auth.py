import hashlib
from typing import Optional


class AuthService:
    def __init__(self):
        self.users = {
            "admin": self._hash_password("admin123"),
            "demo": self._hash_password("demo123")
        }
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> bool:
        if username not in self.users:
            return False
        return self.users[username] == self._hash_password(password)
    
    def register(self, username: str, password: str) -> bool:
        if username in self.users:
            return False
        self.users[username] = self._hash_password(password)
        return True
    
    def get_user_role(self, username: str) -> Optional[str]:
        if username == "admin":
            return "admin"
        elif username == "demo":
            return "user"
        return None