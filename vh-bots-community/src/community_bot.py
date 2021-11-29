from discord.embeds import Embed
import bot_config
import discord
import re

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from settings import *

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='c.', intents=intents)
bot.remove_command('help') # Will replace this with our custom help command

CONFIG = bot_config.BotConfig(bot=bot)

initial_extensions = ['redemption_cog', 'member_cog', 'listener_cog', 'background_cog', 'general_cog', 'settings_cog']
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.command(name='help')
@commands.dm_only()
async def help(ctx, flag: str=None):
    is_admin = CogHelpers.check_is_admin(ctx)
    flag = None if flag is None else flag.strip()
    admin_help = (not flag is None and flag.lower() == 'admin')

    help_text_lines = []
    help_text_lines.append("Welcome to the VH Community Bot!\n")

    commands = [
        {
            'name': "General",
            'public_commands': ['c.help', 'c.join'],
            'admin_commands': ['c.reload', 'c.settings']
        },
        {
            'name': "Rewards",
            'public_commands': ['c.rewards', 'c.redeem', 'c.balance'],
            'admin_commands': ['c.addreward', 'c.setreward']
        },
        {
            'name': "Guild Members",
            'public_commands': [],
            'admin_commands': ['c.award', 'c.lookup', 'c.setbalance']
        },
        {
            'name': "Point Awards",
            'public_commands': [],
            'admin_commands': ['c.pendingawards']
        }
    ]

    help_embed = EmbedBuilder().setTitle("Villager Haven Community Bot Help") \
                .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)

    if not flag is None and flag.startswith("c."):
        command_list = [cmd for cat_cmds in commands for cmd in cat_cmds['public_commands']]
        if is_admin:
            command_list.extend([cmd for cat_cmds in commands for cmd in cat_cmds['admin_commands']])

        if not flag in command_list:
            help_text_lines.append("Unknown command: `{0}`".format(flag))
        else:
            help_text_lines.append("`{0}` - test".format(flag))
        
        help_embed = help_embed.setDescriptionFromLines(help_text_lines)
    else:
        help_text_lines.append("See below for a list of modules and the commands that are available "
                                "in each.  For more information on a specific command, you can use "
                                "`c.help <command>` (e.g. `c.help c.shop`)\n")
        help_text_lines.append("Most commands must be run in DMs, unless otherwise noted.\n")

        if is_admin:
            if not admin_help:
                help_text_lines.append("To view the list of bot admin commands, use `c.help admin`\n")
            else:
                help_text_lines.append("**__You are currently viewing bot admin commands.__**")
                help_text_lines.append("To view the list of public commands, use `c.help`\n")

        help_embed = help_embed.setDescriptionFromLines(help_text_lines) \
                                .addSpacerField()

        commands_key = '{0}_commands'.format('admin' if admin_help else 'public')
        commands.sort(key=lambda c: len(c[commands_key]))

        for command_category in commands:
            display_commands = ['{0} {1}'.format('-' if admin_help else '+', cmd) for cmd in command_category[commands_key]]
            if len(display_commands) == 0:
                continue

            help_embed = help_embed.addField({
                'name': command_category['name'],
                'value': "```diff\n{0}\n```".format('\n'.join(display_commands))
            })

    await ctx.send(embed=help_embed.build())

@bot.command(name='reload')
@commands.check(CogHelpers.check_is_admin)
async def reload(ctx):
    for extension in initial_extensions:
        bot.reload_extension(extension)

    await ctx.message.author.send(content='Reloaded the queue bot!')

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