import disnake
from disnake.ext import commands
from config import *

bot = commands.Bot(command_prefix='!', help_command=None, intents=disnake.Intents.all())


@bot.event
async def on_ready():
    print("Бот готов!")


bot.load_extension('cogs.Moderation')
bot.load_extension('cogs.Database')
bot.load_extension('cogs.Help')
bot.run(token)
