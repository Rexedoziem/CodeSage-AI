import aiosqlite

class UserStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create_user(self, username: str, hashed_password: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed_password)
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_user(self, username: str):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT username, password FROM users WHERE username = ?",
                (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {'username': row[0], 'password': row[1]}
                return None