import disnake
from disnake.ext import commands
from random import randrange
import re
import sqlite3
import pymorphy3
from config import token, filt

db = sqlite3.connect('Main.db')
c = db.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER,
    name TEXT,
    warns INTEGER,
    level INTEGER
)""")
c.execute("""CREATE TABLE IF NOT EXISTS words (
    word TEXT
)
""")

db.commit()
bot = commands.Bot(command_prefix='!', help_command=None, intents=disnake.Intents.all())
morph = pymorphy3.MorphAnalyzer()


@bot.event
async def on_ready():
    print(f'Работаем братья')
    for guild in bot.guilds:
        for member in guild.members:
            if c.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                c.execute(f'INSERT INTO users VALUES({member.id}, "{member}", 0, 0)')
                db.commit()
            else:
                pass


@bot.event
async def on_member_join(member):
    c.execute("INSERT INTO users VALUES ('user, 0')")
    for guild in bot.guilds:
        for member in guild.members:
            if c.execute(f"SELECT id FROM users WHERE id = {member.id}").fetchone() is None:
                c.execute(f'INSERT INTO users VALUES({member.id}, "{member}", 0, 0)')
                db.commit()
            else:
                pass


@bot.event
async def on_message(message):
    br = False
    c.execute("SELECT word FROM words")
    sensored = c.fetchall()
    if filt:
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
                            br = True
                            break


@bot.slash_command(name='view_warns', description='Добавить запрещенные слова')
async def my_warns(ctx):
    await ctx.send(f'У тебя {c.execute(f"SELECT warns FROM users WHERE id = {ctx.author.id}").fetchone()[0]} варн')


@bot.slash_command(name='add_sensored', description='Добавить запрещенные слова')
@commands.has_permissions(administrator=True)
async def word_add(ctx, message):
    if ',' in message:
        message = re.sub(',', '', message)
    words = message.split()
    for word in words:
        c.execute(f"INSERT INTO words VALUES('{word}')")
        db.commit()
    await ctx.send(f'В запрещенные слова добавлено: {",".join(words)}')


#
#
# @commands.has_permissions(administrator=True)
# async def spam(ctx, message):
#     while spam:
#         await ctx.send(f'{message}')
#
#
# @bot.slash_command(description='Кинуть кубик d2')
# async def d2(ctx):
#     await ctx.send(f'И вам выпадает... {randrange(1, 2)} из 2')
#
#
# @bot.slash_command(description='Кинуть кубик d6')
# async def d6(ctx):
#     await ctx.send(f'И вам выпадает... {randrange(1, 6)} из 6')
#
#
# @bot.slash_command(description='Кинуть кубик d20')
# async def d20(ctx):
#     await ctx.send(f'И вам выпадает... {randrange(1, 20)} из 20')


bot.run(token)

db.close()
