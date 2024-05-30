import disnake
from disnake.ext import commands
import sqlite3
from config import database


class Database(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.create_table()

    async def create_table(self):
        db = sqlite3.connect(database)
        c = db.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER,
            name TEXT,
            warns INTEGER,
            level INTEGER,
            time INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS words (
            word TEXT
        )
        """)
        db.commit()
