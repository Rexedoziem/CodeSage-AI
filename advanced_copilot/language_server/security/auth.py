import jwt
from datetime import datetime, timedelta, timezone
from .encryption import encrypt, verify_password
from .user_store import UserStore
import logging

class AuthManager:
    def __init__(self, secret_key: str, user_store: UserStore):
        self.secret_key = secret_key
        self.user_store = user_store

    async def register_user(self, username: str, password: str) -> bool:
        if await self.user_store.get_user(username):
            return False
        hashed_password = encrypt(password)
        return await self.user_store.create_user(username, hashed_password)

    async def authenticate_user(self, username: str, password: str) -> str:
        user = await self.user_store.get_user(username)
        if not user or not verify_password(password, user['password']):
            return None
        return self.generate_token(username)

    def generate_token(self, username: str) -> str:
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            'username': username,
            'exp': expiration
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['username']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    async def check_permissions(self, token: str, permission: str) -> bool:
        username = self.verify_token(token)
        if not username:
            return False
        user = await self.user_store.get_user(username)
        if not user or permission not in user.get('permissions', []):
            return False
        return True

    def log_security_event(self, event_type: str, message: str, user_id: int = None):
        logger = logging.getLogger(__name__)
        logger.info(f"Security Event: {event_type} - {message}")