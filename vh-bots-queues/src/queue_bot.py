import bot_config
import discord
import re

from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='q.', intents=intents)
bot.remove_command('help') # Will replace this with our custom help command

CONFIG = bot_config.BotConfig(bot=bot)

initial_extensions = ['queue_cog', 'mgi_cog']
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

def can_reload(ctx):
    user_id = ctx.message.author.id

    member = CONFIG.get_guild_member(user_id)
    if member is None:
        return False

    for member_role in member.roles:
        if member_role.id in CONFIG.OWNER_ROLES:
            return True
    
    return False

def can_create_queue(ctx):
    user_id = ctx.message.author.id

    member = CONFIG.get_guild_member(user_id)
    if member is None:
        return False
    
    if member.id in CONFIG.CREATE_QUEUE_USERS:
        return True

    for member_role in member.roles:
        if member_role.id in CONFIG.CREATE_QUEUE_ROLES:
            return True
    
    return False

def is_events_team(ctx):
    user_id = ctx.message.author.id

    member = CONFIG.get_guild_member(user_id)
    if member is None:
        return False

    for member_role in member.roles:
        if member_role.id == CONFIG.EVENTS_TEAM_ROLE:
            return True
    
    return False

@bot.command(name='help')
@commands.dm_only()
async def help(ctx):
    help_text = """
Welcome to the VH Queue Bot!

See below for commands you can use.  Please note that to use the Queue Bot, you must be a member of Villager Haven.
Commands can only be used in DMs.

```
q.gameinfo      View or set the game info for your account
q.queues        View the currently active queues
q.join <code>   Join the queue with the specified queue ID
q.status        View your current queue position and queue size
q.report <msg>  Report an issue with the queue you are currently up for
q.leave         Leave your current queue or end your trip
```
"""

    if can_create_queue(ctx):
        help_text += """
Commands for users who can create/manage queues are below.
These commands, *except* q.kick, can only be used in DMs.

```
q.create        Create a new queue.  Queues are locked by default
q.close         Closes your queue.  This removes all queue members, unless it is currently their turn
q.dodo          Update the Dodo code for your queue
q.end           End your queue.  This deletes the queue and can only be done when the queue is empty
"""
        if is_events_team(ctx):
            help_text += """q.end <id>      (EVENTS TEAM ONLY) - This force deletes the queue with the specified queue ID
"""

        help_text += """q.gameinfo <id> Lookup game info for the specified user ID
q.kick <user>   Kick the specified user from the queue.  This command needs to be run in the queue channel
q.list          View the currently active users and the next 10 in line for your queue
q.message       Send a DM message to everyone currently in your queue
q.lock          Lock your queue and prevent new users from joining
q.unlock        Unlock your queue and allow new users to join
```
"""

    await ctx.send(content=help_text)
    await ctx.invoke(bot.get_command('queues'))

@bot.command(name='reload')
@commands.check(can_reload)
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
    await bot.change_presence(activity=discord.Game(name='line-leader || q.help'))

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