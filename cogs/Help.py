import disnake
from disnake.ext import commands
import datetime
import re
import sqlite3
from config import *
from disnake.enums import ButtonStyle

bot = commands.Bot(command_prefix='!', help_command=None, intents=disnake.Intents.all())


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @bot.slash_command(name='help', description='Посмотреть свои варны')
    async def help(self, ctx):
        db = sqlite3.connect(database)
        c = db.cursor()
        view = HelpButtons()
        emb = disnake.Embed(
            title='Помощь в управлении ботом',
            description='Выберите, с чем вам нужна помощь.')
        emb.set_author(
            name='Source bot',
            url='https://github.com/Zhabich12/Moderation-system-bot-by-Zhabich12'
        )
        await ctx.send(embed=emb, view=view)

        db.commit()
        db.close()

class HelpButtons(disnake.ui.View):
    def __init__(self, *, timeout: float | None = 180) -> None:
        super().__init__(timeout=timeout)
    
    @disnake.ui.button(label='О командах', style=ButtonStyle.red)
    async def commands(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        db = sqlite3.connect(database)
        c = db.cursor()
        try:
            warns = c.execute("SELECT warns_for_mute FROM guild_config WHERE server_id = ?",
                            (inter.guild_id,)).fetchall()
            emb = disnake.Embed(
                title='Все команды',
                description=f'/my_warns - посмотреть кол-во своих варнов. Доступно от 0 уровня\n /other_warns - посмотреть кол-во варнов других участников. Доступно от 1 уровня'
                f'\n /ban_words - внести слово/слова в список запрещённых. Доступно от 2 уровня \n /unban - удалить слово/слова из списка запрещённых \n'
                f'/give_mute - выдать мут нарушителю. Доступно только от 1 уровня и в случае наличия {warns[0][0]} варнов у нарушителя.'
                f'/set_level - выдать участинику определённый уровень. Доступно от 3 уровня.\n /delete_warn - удалить варн у участника. Доступно от 1 уровня.')
            emb.set_author(
                name='Source bot code',
                url='https://github.com/Zhabich12/Moderation-system-bot-by-Zhabich12'
            )
            or_message = inter.message.id
            await inter.message.edit(embed=emb, view=BackButtons())
        except EOFError as e:
            inter.send(f'Данное сообщение не является актуальным. Пропишите команду /help заново', ephemeral=True)
        db.commit()
        db.close()
    @disnake.ui.button(label='О модерации и фильтре', style=ButtonStyle.red)
    async def system(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        db = sqlite3.connect(database)
        c = db.cursor()
        try:    
            emb = disnake.Embed(
                title='Модерация и фильтр'
            )
            emb.add_field(name='Модерация', value=f'У каждого участника есть свой уровень в боте, стандартно - 0. Уровень определяет к каким командам участник имеет пользователь. Уровни и доступ к'
                f'командам. Максимальный уровень - 3. Уровень может выдавать только владелец сервера или участник с 3 уровнем.')
            emb.add_field(name='Фильтр', value=f'Если в сообщении будет слово, внесённое в запрещённый список, то фильтр удалит его и выдаст варн нарушителю. Также'
                        f'не еадо писать слова в разных формах, фильтр автоматически ставит всё в начальную форму.')
            emb.set_author(
                name='Source bot code',
                url='https://github.com/Zhabich12/Moderation-system-bot-by-Zhabich12')
            or_message = inter.message.id
            await inter.message.edit(embed=emb, view=BackButtons())
        except EOFError as e:
            inter.send(f'Данное сообщение не является актуальным. Пропишите команду /help заново', ephemeral=True)
        db.commit()
        db.close()
class BackButtons(disnake.ui.View):
    def __init__(self, *, timeout: float | None = 180) -> None:
        super().__init__(timeout=timeout)
    
    @disnake.ui.button(label='Назад', style=ButtonStyle.red)
    async def commands(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        db = sqlite3.connect(database)
        c = db.cursor()
        try:
            emb = disnake.Embed(
                title='Помощь в управлении ботом',
                description='Выберите, с чем вам нужна помощь.')
            emb.set_author(
                name='Source bot',
                url='https://github.com/Zhabich12/Moderation-system-bot-by-Zhabich12'
            )
            or_message = inter.message.id
            await inter.message.edit(embed=emb, view=HelpButtons())
        except EOFError as e:
            inter.send(f'Данное сообщение не является актуальным. Пропишите команду /help заново', ephemeral=True)
        db.commit()
        db.close()

def setup(bot: commands.Bot):
    bot.add_cog(Help(bot))
