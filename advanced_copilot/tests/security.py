import unittest
from unittest.mock import patch, MagicMock
import asyncio
from datetime import datetime, timezone
from advanced_copilot.language_server.security.auth import AuthManager
from advanced_copilot.language_server.security.encryption import encrypt, decrypt, verify_password

class TestSecurity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_user = {"username": "testuser", "password": "testpass"}
        self.test_data = "sensitive information"
        self.test_permissions = ["read", "write"]
        self.auth_manager = AuthManager("secret_key", MagicMock())

    async def test_encryption(self):
        encrypted = encrypt(self.test_data)
        self.assertNotEqual(encrypted, self.test_data)
        decrypted = decrypt(encrypted)
        self.assertEqual(decrypted, self.test_data)

    @patch('advanced_copilot.language_server.security.auth.verify_password')
    async def test_authentication(self, mock_verify):
        mock_verify.return_value = True
        self.auth_manager.user_store.get_user = AsyncMock(return_value=self.test_user)

        result = await self.auth_manager.authenticate_user(self.test_user["username"], self.test_user["password"])
        
        self.assertIsNotNone(result)
        mock_verify.assert_called_once_with(self.test_user["password"], self.test_user["password"])

    @patch('advanced_copilot.language_server.security.auth.AuthManager.verify_token')
    async def test_authorization(self, mock_verify_token):
        mock_verify_token.return_value = self.test_user["username"]
        self.auth_manager.user_store.get_user = AsyncMock(return_value={"permissions": self.test_permissions})

        result = await self.auth_manager.check_permissions("fake_token", "write")
        
        self.assertTrue(result)
        mock_verify_token.assert_called_once_with("fake_token")

    def test_logging(self):
        with patch('logging.Logger.info') as mock_log:
            self.auth_manager.log_security_event("User login", self.test_user["username"])
            mock_log.assert_called_once_with(f"Security Event: User login - {self.test_user['username']}")

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

if __name__ == '__main__':
    unittest.main()