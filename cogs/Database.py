import disnake
from disnake.ext import commands
import sqlite3
from config import database

bot = commands.Bot(command_prefix='!', help_command=None, intents=disnake.Intents.all())


class Database(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.create_table()

    def create_table(self):
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

    @commands.Cog.listener()
    async def on_ready(self):
        db = sqlite3.connect(database)
        c = db.cursor()
        print(f'Работаем братья')
        for guild in self.bot.guilds:
            for member in guild.members:
                if c.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                    c.execute(f'INSERT INTO users VALUES({member.id}, "{member}", 0, 0, 0)')
                    db.commit()
                else:
                    pass
        db.close()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        db = sqlite3.connect(database)
        c = db.cursor()
        c.execute("INSERT INTO users VALUES ('user, 0')")
        for guild in self.bot.guilds:
            for member in guild.members:
                if c.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                    c.execute(f'INSERT INTO users VALUES({member.id}, "{member}", 0, 0, 0)')
                    db.commit()
                else:
                    pass
        db.close()

    async def give_warn(self, message: disnake.Message):
        db = sqlite3.connect(database)
        c = db.cursor()
        c.execute(f"UPDATE users SET warns = warns + 1 WHERE id = {message.author.id}")
        db.commit()
        db.close()


def setup(bot: commands.Bot):
    bot.add_cog(Database(bot))
