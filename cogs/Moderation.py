import disnake
from disnake.ext import commands
import datetime
import re
import sqlite3
import pymorphy3
from config import author, database

bot = commands.Bot(command_prefix='!', help_command=None, intents=disnake.Intents.all())
morph = pymorphy3.MorphAnalyzer()


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        db = sqlite3.connect(database)
        br = False
        c = db.cursor()
        c.execute("SELECT word FROM words")
        sensored = c.fetchall()
        if not message.author.bot and (c.execute("SELECT filter FROM guild_config WHERE server_id = ?",
                                                 (message.guild.id,)).fetchone()[0] > 0):
            user_message = message.content.split()
            for content in user_message:
                if br:
                    break
                content = morph.parse(content)[0].normal_form
                for sensoreds in sensored:
                    sensoreds = sensoreds[0]
                    sensoreds = morph.parse(sensoreds)[0].normal_form
                    if content.lower() == sensoreds.lower():
                        await message.channel.send(f'{message.author.mention}')
                        await message.delete()
                        c.execute(
                            "UPDATE users SET warns = warns + 1 WHERE id = ? AND server_id = ?",
                            (message.author.id, message.guild.id)
                        )
                        db.commit()
                        br = True
                        break
        db.close()

    @bot.slash_command(name='view_warns', description='Посмотреть свои варны')
    async def my_warns(self, ctx):
        db = sqlite3.connect(database)
        c = db.cursor()
        warns = c.execute("SELECT warns FROM users WHERE id = ? AND server_id = ?",
                          (ctx.author.id, ctx.guild.id)).fetchone()
        await ctx.send(f'Количество варнов: {warns[0] if warns else 0}')
        db.close()

    @bot.slash_command(name='view_member_warns', description='Посмотреть варны участника.')
    async def other_warns(self, ctx, member: disnake.Member):
        db = sqlite3.connect(database)
        c = db.cursor()
        warns = c.execute("SELECT warns FROM users WHERE id = ? AND server_id = ?",
                          (member.id, ctx.guild.id)).fetchone()
        await ctx.send(f'Количество варнов: {warns[0] if warns else 0}')
        db.close()

    @bot.slash_command(name='ban_words', description='Добавить запрещенные слова')
    async def ban_words(self, ctx, message):
        db = sqlite3.connect(database)
        c = db.cursor()
        level = c.execute("SELECT level FROM users WHERE id = ? AND server_id = ?",
                          (ctx.author.id, ctx.guild.id)).fetchone()
        db_words = c.execute("SELECT word FROM words WHERE server_id = ?",
                             (ctx.guild.id,)).fetchall()
        new_words = []
        not_new_words = []
        if sum([len(i[0]) for i in db_words]) > 2000:
            await ctx.send(f'На сервере превышено максимальное количество заблокированных слов', ephermal=True)
        elif level and level[0] >= 2:
            if ',' in message:
                message = re.sub(',', '', message)
            words = message.split()
            for word in words:
                if word.lower() not in [i[0].lower() for i in db_words]:
                    c.execute("INSERT INTO words VALUES(?, ?)", (word.lower(), ctx.guild.id))
                    new_words.append(word.lower())
                    db.commit()
                else:
                    not_new_words.append(word.lower())
            if (len(new_words)) > 0 and (len(not_new_words) < 1):
                await ctx.send(f'В запрещенные слова добавлено: {', '.join(new_words)}.')
            elif (len(new_words) > 0) and (len(not_new_words) > 0):
                ans = f'Следующие слова: {', '.join(not_new_words)} уже под запретом'
                await ctx.send(f'В запрещенные слова добавлено: {', '.join(new_words)}.{ans}')
            else:
                ans = f'Слова {', '.join(not_new_words)} уже под запретом'
                await ctx.send(f'{ans}')
        else:
            await ctx.send(f'Ваш уровень слишком мал для этого действия.')
        db.close()

    @bot.slash_command(name='unban_words', description='Удалить слова из запрета.')
    async def unban(self, ctx, message):
        db = sqlite3.connect(database)
        c = db.cursor()
        del_words = []
        undel_words = []
        if ',' in message:
            message = re.sub(',', '', message)
        words = message.split()
        db_words = [i[0] for i in c.execute("SELECT word FROM words WHERE server_id = ?",
                                            (ctx.guild.id,)).fetchall()]
        for db_word in db_words:
            for word in words:
                if word == db_word:
                    c.execute("DELETE FROM words WHERE word = ? AND server_id = ?",
                              (word, ctx.guild.id))
                    db.commit()
                    del_words.append(word)
                else:
                    if word in undel_words:
                        pass
                    elif word in (i for i in db_words):
                        pass
                    else:
                        undel_words.append(word)
        embed = disnake.Embed(title='Удаление слов из запрета',
                              description=f'Были удалены следующие слова: {', '.join(del_words)}'
                                          f'\n Не удалось удалить следущие слова: {', '.join(undel_words)}',
                              color=disnake.Color.blue())
        await ctx.send(embed=embed)
        db.close()

    @bot.slash_command(name='give_mute', description='Дать мут нарушителю.')
    async def mute(self, ctx, member: disnake.Member):
        db = sqlite3.connect(database)
        c = db.cursor()
        try:
            # из базы данных берется кол-во варнов того, кому выдается мут
            warns = c.execute("SELECT warns FROM users WHERE id = ? AND server_id = ?",
                              (member.id, ctx.guild.id)).fetchone()
            # из базы данных берется уровень того, кто вызвал команду
            author_level = c.execute("SELECT level FROM users WHERE id = ? AND server_id = ?",
                                     (ctx.author.id, ctx.guild.id)).fetchone()
            # из базы данных берется уровень того, кому выдается мут
            member_level = c.execute("SELECT level FROM users WHERE id = ? AND server_id = ?",
                                     (member.id, ctx.guild.id)).fetchone()
            if author_level and author_level[0] >= 1:
                if member_level and member_level[0] > author_level[0]:
                    await ctx.send(f'У этого пользователя уровень выше, чем у вас')
                elif warns[0] < c.execute("SELECT warns_for_mute FROM guild_config WHERE server_id = ?",
                                          (ctx.guild.id, )).fetchone()[0]:
                    await ctx.send(f'Данный участник не получил нужное количество варнов для мута')
                else:
                    time = datetime.datetime.now() + datetime.timedelta(hours=6)
                    await member.timeout(until=time)
                    await ctx.send(f'Выдан мут участнику {member}')
            else:
                await ctx.send(f'У вас недостаточно прав для выдачи мутов')
        except sqlite3.Error as e:
            await ctx.send(
                f'Не удалось выдать мут. Возможно тот, кому вы хотите его выдать обладает правами администратора.')
        db.close()

    @bot.slash_command(name='set_level', description='Назначить уровень.')
    async def set_lvl(self, ctx, member: disnake.Member, lvl: int):
        db = sqlite3.connect(database)
        c = db.cursor()
        author_level = c.execute("SELECT level FROM users WHERE id = ? AND server_id = ?",
                                 (ctx.author.id, ctx.guild.id)).fetchone()
        if author_level and author_level[0] >= 3:
            c.execute("UPDATE users SET level = ? WHERE id = ? AND server_id = ?",
                      (lvl, member.id, ctx.guild.id))
            db.commit()
            await ctx.send(f'Теперь уровень {member} - {lvl}')
        elif ctx.author.id == author:
            c.execute("UPDATE users SET level = ? WHERE id = ? AND server_id = ?",
                      (lvl, member.id, ctx.guild.id))
            db.commit()
            await ctx.send(f'Теперь уровень {member} - {lvl}')
        else:
            await ctx.send(f'У вас слишком низкий уровень для этого действия.')
        db.close()

    @bot.slash_command(name='delete_warn', description='Удалить варн.')
    async def warned(self, ctx, member: disnake.Member):
        db = sqlite3.connect(database)
        c = db.cursor()
        author_level = c.execute("SELECT level FROM users WHERE id = ? AND server_id = ?",
                                 (ctx.author.id, ctx.guild.id)).fetchone()
        if author_level and author_level[0] > 0:
            c.execute("UPDATE users SET warns = warns - 1 WHERE id = ? AND server_id = ?",
                      (member.id, ctx.guild.id))
            db.commit()
        else:
            await ctx.send('Твой уровень слишком мал для этого действия.')
        db.close()

    @bot.slash_command(name='view_banned_words', description='Посмотреть запрещенные слова.')
    async def view_words(self, interaction):
        db = sqlite3.connect(database)
        c = db.cursor()
        words = c.execute("SELECT word FROM words WHERE server_id = ?",
                          (interaction.guild.id,)).fetchall()
        view = ''
        total_simvols = 0
        for i, word in enumerate(words):
            if total_simvols + len(word[0]) >= 2000:
                break
            if i + 1 < len(words):
                view += f'{i + 1}.{word[0]}, '
            else:
                view += f'{i + 1}.{word[0]}'
            total_simvols += len(word[0])
        embed = disnake.Embed(title="Запрещенные слова", description=view, color=disnake.Color.blue())
        await interaction.response.send_message(embed=embed)
        db.close()

    @bot.slash_command(name='set_warns_for_mute', description='Установить кол-во варнов для мута.')
    async def set_warns_for_mute(self, interaction, warns):
        db = sqlite3.connect(database)
        c = db.cursor()
        c.execute("UPDATE guild_config SET warns = ? WHERE server_id = ?",
                  (warns, interaction.guild.id))
        db.commit()
        db.close()

    @bot.slash_command(name='filter_on', description='Включить фильтрацию чата.')
    async def filter_on(self, interaction):
        db = sqlite3.connect(database)
        c = db.cursor()
        if c.execute("SELECT filter FROM guild_config WHERE server_id = ?",
                     (interaction.guild.id,)).fetchone() == 1:
            interaction.response.send_message(f'У вас уже включена фильтрация чата.')
        else:
            c.execute("UPDATE guild_config SET filter = ? WHERE server_id = ?",
                      (1, interaction.guild.id))
            await interaction.response.send_message(f'Успешно!')
        db.commit()
        db.close()

    @bot.slash_command(name='filter_off', description='Выключить фильтрацию чата.')
    async def filter_off(self, interaction):
        db = sqlite3.connect(database)
        c = db.cursor()
        if c.execute("SELECT filter FROM guild_config WHERE server_id = ?",
                     (interaction.guild.id,)).fetchone() == 0:
            interaction.response.send_message(f'У вас уже выключена фильтрация чата.')
        else:
            c.execute("UPDATE guild_config SET filter = ? WHERE server_id = ?",
                      (0, interaction.guild.id))
            await interaction.response.send_message(f'Успешно!')
        db.commit()
        db.close()

    @bot.slash_command(name='delete_messages',
                       description='Начать чистку сообщений в канале.')
    async def delete_messages(self, interaction, limit=100):
        db = sqlite3.connect(database)
        c = db.cursor()
        if c.execute("SELECT level FROM users WHERE id = ? AND server_id = ?",
                        (interaction.author.id, interaction.guild.id)).fetchone()[0] > 0:
            await interaction.message.Channel.purge(limit=limit)
        db.commit()
        db.close()

    @bot.slash_command(name='delete_message', description='Для удаления сообщения введите эту команду ответом на сообщение, которое вы хотите удалить.')
    async def delete_message(self, ctx):
        db = sqlite3.connect(database)
        if ctx.message.reference:
            a = ctx.message.reference.message_id
            ctx.interaction.delete_message(a)
        db.commit()
        db.close()


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot))
