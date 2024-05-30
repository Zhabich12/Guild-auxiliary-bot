import disnake
from disnake.ext import commands
from config import token

bot = commands.Bot(command_prefix='!', help_command=None, intents=disnake.Intents.all())


@bot.event
async def on_ready():
    print("Бот готов!")


bot.load_extension('cogs.Moderation')

bot.run(token)

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

