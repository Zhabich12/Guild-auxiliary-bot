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
            time INTEGER,
            server_id INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS words (
            word TEXT,
            server_id INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS guild_config (
            server_id INTEGER,
            filter INTEGER,
            warns_for_mute INTEGER
        )""")
        db.commit()
        db.close()

    @commands.Cog.listener()
    async def on_ready(self):
        db = sqlite3.connect(database)
        c = db.cursor()
        print(f'Работаем братья')
        for guild in self.bot.guilds:
            if c.execute("SELECT server_id FROM guild_config WHERE server_id = ?",
                         (guild.id, )).fetchone() is None:
                c.execute("INSERT INTO guild_config (server_id, filter, warns_for_mute) VALUES (?, ?, ?)",
                          (guild.id, 0, 5))
                db.commit()
            for member in guild.members:
                if c.execute("SELECT id FROM users WHERE id = ? AND server_id = ?",
                             (member.id, guild.id)).fetchone() is None:
                    c.execute("INSERT INTO users (id, name, warns, level, time, server_id) VALUES (?, ?, ?, ?, ?, ?)",
                              (member.id, str(member), 0, 0, 0, guild.id))
                    db.commit()
        db.close()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        db = sqlite3.connect(database)
        c = db.cursor()
        if c.execute("SELECT id FROM users WHERE id = ? AND server_id = ?",
                     (member.id, member.guild.id)).fetchone() is None:
            c.execute("INSERT INTO users (id, name, warns, level, time, server_id) VALUES (?, ?, ?, ?, ?, ?)",
                      (member.id, str(member), 0, 0, 0, member.guild.id))
            db.commit()
        db.close()


def setup(bot: commands.Bot):
    bot.add_cog(Database(bot))
