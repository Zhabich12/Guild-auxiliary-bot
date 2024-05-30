import disnake
from disnake.ext import commands
import datetime
import re
import sqlite3
import pymorphy3
from config import author, database

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
bot = commands.Bot(command_prefix='!', help_command=None, intents=disnake.Intents.all())
morph = pymorphy3.MorphAnalyzer()


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Работаем братья')
        for guild in bot.guilds:
            for member in guild.members:
                if c.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                    c.execute(f'INSERT INTO users VALUES({member.id}, "{member}", 0, 0, 0)')
                    db.commit()
                else:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        c.execute("INSERT INTO users VALUES ('user, 0')")
        for guild in bot.guilds:
            for member in guild.members:
                if c.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                    c.execute(f'INSERT INTO users VALUES({member.id}, "{member}", 0, 0, 0)')
                    db.commit()
                else:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message):
        br = False
        c.execute("SELECT word FROM words")
        sensored = c.fetchall()
        if not message.author.bot:
            user_message = message.content.split()
            for content in user_message:
                if br:
                    break
                content = morph.parse(content)[0].normal_form
                for sensoreds in sensored:
                    if br:
                        break
                    else:
                        sensoreds = sensoreds[0]
                        sensoreds = morph.parse(sensoreds)[0].normal_form
                        if content.lower() == sensoreds.lower():
                            await message.channel.send(f'{message.author.mention}')
                            await message.delete()
                            c.execute(f"UPDATE users SET warns = warns + 1 WHERE id = {message.author.id}")
                            db.commit()
                            br = True
                            break

    @bot.slash_command(name='view_warns', description='Посмотреть свои варны')
    async def my_warns(self, ctx):
        await ctx.send(
            f'Количество варнов: {c.execute(f"SELECT warns FROM users WHERE id = {ctx.author.id}").fetchone()[0]}')

    @bot.slash_command(name='view_member_warns', description='Посмотреть варны участника.')
    async def other_warns(self, ctx, member: disnake.Member):
        await ctx.send(
            f'Количество варнов: {c.execute(f"SELECT warns FROM users WHERE id = {member.id}").fetchone()[0]} ')

    @bot.slash_command(name='ban_words', description='Добавить запрещенные слова')
    async def word_add(self, ctx, message):
        if c.execute(f"SELECT level FROM users WHERE id = {ctx.author.id}").fetchone()[0] >= 2:
            if ',' in message:
                message = re.sub(',', '', message)
            words = message.split()
            for word in words:
                c.execute(f"INSERT INTO words VALUES('{word}')")
                db.commit()
            await ctx.send(f'В запрещенные слова добавлено: {",".join(words)}')
        else:
            await ctx.send(f'Ваш уровень слишком мал для этого действия.')

    @bot.slash_command(name='give_mute', description='Дать мут нарушителю.')
    async def mute(self, ctx, member: disnake.Member):
        try:
            warns = c.execute(f"SELECT warns FROM users WHERE id = {member.id}").fetchone()[0]
            if c.execute(f"SELECT level FROM users WHERE id = {ctx.author.id}").fetchone()[0] >= 1:
                a = c.execute(f"SELECT level FROM users WHERE id = {member.id}").fetchone()[0]
                b = c.execute(f"SELECT level FROM users WHERE id = {ctx.author.id}").fetchone()[0]
                if a > b:
                    ctx.send(f'У этого пользователя уровень выше, чем у вас')
                elif warns < 0:
                    ctx.send(f'Данный участник не получил нужное количество варнов для мута')
                else:
                    time = datetime.datetime.now() + datetime.timedelta(hours=int(6))
                    await member.timeout(until=time)
                    await ctx.response.send_message(f'Выдан мут участнику {member}')
            else:
                await ctx.send(f'У вас недостаточно прав для выдачи мутов')
        except:
            await ctx.send(
                f'Не удалось выдать мут. Возможно тот, кому вы хотите его выдать обладает правами администратора.')

    @bot.slash_command(name='set_level', description='Назначить уровень.')
    async def set_lvl(self, ctx, member: disnake.Member, lvl: int):
        if c.execute(f"SELECT level FROM users WHERE id = {ctx.author.id}").fetchone()[0] >= 3:
            c.execute(f"UPDATE users SET level = {lvl} WHERE id = {member.id}")
            db.commit()
            await ctx.send(
                f'Теперь уровень {member} - {c.execute(f"SELECT level FROM users WHERE id = "
                                                       f"{ctx.author.id}").fetchone()[0]}')
        elif ctx.author.id == author:
            c.execute(f"UPDATE users SET level = {lvl} WHERE id = {member.id}")

            db.commit()
            await ctx.send(
                f'Теперь уровень {member} - {c.execute(f"SELECT level FROM users WHERE id = "
                                                       f"{ctx.author.id}").fetchone()[0]}')
        else:
            await ctx.send(f'У вас слишком низкий уровень для этого действия.')

    @bot.slash_command(name='delete_warn', description='Удалить варн.')
    async def warned(self, ctx, member: disnake.Member):
        if c.execute(f"SELECT level FROM users WHERE id = {ctx.author.id}").fetchone()[0] > 0:
            c.execute(f"UPDATE users SET warns = warns - 1 WHERE id = {member.id}")
            db.commit()
        else:
            await ctx.send('Твой уровень слишком мал для этого действия.')

    @bot.slash_command(name='view_sensoreds_words', description='Посмотреть запрещенные слова.')
    async def view_words(self, ctx):
        words = c.execute(f"SELECT word FROM words").fetchall()
        view = ''
        simv = 0
        indx = 1
        for word in words:
            simv += len(word[0])
            if simv >= 79:
                view += f'{indx}.{word[0]}\n'
            else:
                view += f'{indx}.{word[0]}, '
            indx += 1
        await ctx.send(f'```{view}```')


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot))
