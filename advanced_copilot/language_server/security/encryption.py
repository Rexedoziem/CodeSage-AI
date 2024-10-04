from cryptography.fernet import Fernet, InvalidToken
from typing import Union

class EncryptionError(Exception):
    pass

class DecryptionError(Exception):
    pass

class Encryptor:
    def __init__(self, key: Union[bytes, None] = None):
        if key is None:
            key = Fernet.generate_key()
        self.fernet = Fernet(key)

    def get_key(self) -> bytes:
        return self.fernet._signing_key

    def encrypt(self, data: str) -> bytes:
        try:
            return self.fernet.encrypt(data.encode())
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt(self, token: bytes) -> str:
        try:
            return self.fernet.decrypt(token).decode()
        except InvalidToken:
            raise DecryptionError("Invalid token or corrupted data")
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {str(e)}")

    def verify_password(self, password: str, encrypted_password: bytes) -> bool:
        try:
            decrypted_password = self.decrypt(encrypted_password)
            return decrypted_password == password
        except DecryptionError:
            return False

# Global Encryptor instance
global_encryptor = Encryptor()

def encrypt(data: str) -> bytes:
    return global_encryptor.encrypt(data)

def decrypt(token: bytes) -> str:
    return global_encryptor.decrypt(token)

def verify_password(password: str, encrypted_password: bytes) -> bool:
    return global_encryptor.verify_password(password, encrypted_password)