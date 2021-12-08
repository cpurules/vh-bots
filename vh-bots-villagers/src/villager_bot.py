from discord.embeds import Embed
import bot_config
import discord
import re

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help') # Will replace this with a custom help command

CONFIG = bot_config.BotConfig()

initial_extensions = []
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.command(name='help')
@commands.dm_only()
async def help(ctx, flag: str=None):
    pass

@bot.command(name='reload')
@commands.check(CogHelpers.check_is_admin)
async def reload(ctx):
    for extension in initial_extensions:
        bot.reload_extension(extension)

    await ctx.message.author.send(content='Reloaded Villager Bot!')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------------')
    
    bot_guild = CONFIG.GET_GUILD()
    print(bot_guild.name)
    await bot.change_presence(activity=discord.Game(name='Animal Crossing: New Horizons'))

@bot.event
async def on_command_error(ctx, error):
    err = getattr(error, 'original', error)

    if isinstance(err, commands.MissingAnyRole):
        return
    if isinstance(err, commands.PrivateMessageOnly):
        return
    if isinstance(err, commands.CheckFailure):
        await ctx.send(content='You do not have permission to use that command!')
        return
    if isinstance(err, commands.CommandNotFound):
        command = ctx.message.content.split(" ")[0]
        command_safe = re.sub(r'<@!?\d+>', '', command)
        await ctx.send(content="Sorry, I don't know the command {0}".format(command_safe))
        return
    
    raise error

bot.run(CONFIG.TOKEN)