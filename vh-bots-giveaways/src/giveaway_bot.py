import asyncio
import discord
import math
import os
import random
import sys

from config import BotConfig
from discord.ext import commands

bot_token = os.getenv("BOT_TOKEN")
if bot_token is None:
    raise ValueError("BOT_TOKEN environment variable not set!")

CONFIG = BotConfig()
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

initial_extensions = ['admin_cog', 'drawing_cog', 'report_cog']
if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------------')
    await bot.change_presence(activity=discord.Game(name='VH Giveaways'))

@bot.command(name='reload')
@commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
async def reload(ctx):
    # Cancel active tasks since they will be recreated
    bot.get_cog('DrawingCog').cancel_active_tasks()

    for extension in initial_extensions:
        bot.reload_extension(extension)
    await bot.get_cog('DrawingCog').on_ready()
    
    await ctx.message.author.send('Reloaded the giveaway bot!')

@bot.command(name='commands',aliases=['help'])
@commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
async def command_help(ctx, command: str=''):
    if command == '':
        # Show help for all commands
        content = """
See below for a list of all supported Celeste commands.  For more information
about a specific command, type !commands **command** (e.g. !commands drawing)

```
!help/!commands        Shows this help page
!help/!commands <cmd>  Shows help for the specified command

!channel               Creates blank event or giveaway channels
!createteam            Creates blank giveaway team channels
!giveaway              Starts a standard giveaway
!drawing/!drawing2     Starts a customized drawing
!report                Generates a report of courier deliveries
!citreport             Generates a report of courier deliveries (CIT only)
!remind                Posts reminder message for winners and cleans roles
!lock/!unlock          Locks or unlocks giveaway winner channels for user messages
!cleanroles            Removes all giveaway-xxxx roles from the server
!cleanchannels         Removes all winners-xxxx channels from the server
!cleanall              Combined !cleanroles and !cleanchannels command
!cleanteams            Removes all team-xxxx channels from the server
!getspecial            Retrieves the currently set special team role
!setspecial            Sets the special team role
!clearspecial          Clears the special team role
!getcitchannel         Retrieves the current setting for separate CIT channels
!togglecitchannel      Toggles the current setting value for separate CIT channels
!giveall               Give all users in the channel a certain role
```
"""
        await ctx.send(content=content)
    else:
        available_commands = ['help', 'commands', 'channel', 'giveaway', 'drawing', 'drawing2', 'report', 'citreport',
                              'remind', 'cleanroles', 'cleanchannels', 'cleanall', 'getspecial', 'setspecial',
                              'clearspecial', 'getcitchannel', 'togglecitchannel', 'createteam', 'lock', 'unlock',
                              'giveall', 'cleanteams']
        if not command in available_commands:
            await ctx.send(content='Unknown command: {0}.  Use !commands to see available commands.'.format(command))
            return
        
        if command == 'commands' or command == 'help':
            content = """
**!commands [optional: command]** - Shows help page, or information for specified command
**!help [optional: command]** - Shows help page, or information for specified command

**Note**: !commands and !help are interchangeable.

```
command:   optional; the command to get help for
```
"""

        if command == 'channel':
            content = """
**!channel [type] [optional: count]** - Creates blank channels in the specified category

```
type:   either giveaway or event
count:  optional; number of channels to create (default: 1)
```
"""

        if command == 'createteam':
            content = """
**!createteam <team name> <member> <member> ...** - Creates giveaway team channels with the specified members.
Appropriate permissions will be granted when the channel is created.

**Note**:  You must include at least one supplier and one courier in a team channel.

```
<team name>:  the name of the team (e.g. charlie-grace, tama, ...), used for channel name
<member>:     a member to add to the team.  can use ping, Discord ID, or Discord username
```
"""

        if command == 'giveaway':
            content = """
**!giveaway [prize]** - Creates a standard giveaway for the specified prize.
This is shorthand for **!drawing giveaway 200w 24h 24h [prize]**

```
prize:   the prize for the winners
```
"""

        if command == 'drawing' or command == 'drawing2':
            content = """
**!drawing [type] [winners] [length] [claim] [prize]** - Creates a custom drawing.
**!drawing2 [type] [winners] [length] [claim] [prize]** - Creates a custom, special drawing.

Special drawings will add the set special team role to the channel and will not add couriers/suppliers to giveaway channels.

```
type:    giveaway or event
winners: number of winners pulled.   format:  ###w
length:  how long you can enter.     format:  ##[d/h/m/s]
claim:   how long winners can claim. format:  ##[d/h/m/s]
prize:   the prize for the winners
```
"""

        if command == 'report' or command == 'citreport':
            content = """
**!report [id]** - Generates a report of courier deliveries (all couriers)
**!citreport [id]** - Generates a report of courier deliveries (CIT only)

```
id:   individual channel id OR 4-character random id
```
"""

        if command == 'remind':
            content = """
**!remind [time]** - Posts a reminder message and removes roles from delivered-to winners.
This will only remove roles from winners whose message has both a \N{WHITE HEAVY CHECK MARK} and \N{CROSS MARK} reaction.

```
time:   length of time remaining to claim. format: ###[d/h/m/s]
```
"""

        if command == 'cleanroles':
            content = """
**!cleanroles [optional: id]** - Removes **giveaway-xxxx** and **event-xxxx** roles from the server.

```
id:   optional; the 4-character role ID to remove
      if left blank, will remove all giveaway/event roles
```
"""

        if command == 'cleanchannels':
            content = """
**!cleanchannels [optional: id]** - Removes **winners-xxxx** channels from the server.

```
id:   optional; the 4-character channel ID to remove
      if left blank, will remove all winners channels
```
"""

        if command == 'cleanall':
            content = """
**!cleanall [optional: id]** - Removes all giveaway/event channels and roles.
This is the same as doing **!cleanroles [id]** and then **!cleanchannels [id]**

```
id:   optional; the 4-character channel/role ID to remove
      if left blank, will remove all winner roles and channels
```
"""

        if command == 'cleanteams':
            content = """
**!cleanteams** - Removes all giveaway team channels.
This deletes any channel that starts with `teams-`
"""

        if command == 'getspecial':
            content = """
**!getspecial** - Retrieves the currently set special team role.  This is the role that will be added to channels for special drawings.
"""

        if command == 'setspecial':
            content = """
**!setspecial <role>** - Sets the special team role to the mentioned role.

```
role:  the name or mention of the special team role
```
"""

        if command == 'clearspecial':
            content = """
**!clearspecial** - Clears the set special team role.
"""

        if command == 'getcitchannel':
            content = """
**!getcitchannel** - Gets the current setting value for whether a separate CIT/mentor channel is created
"""

        if command == 'togglecitchannel':
            content = """
**!togglecitchannel** - Toggles the setting value for whether a separate CIT/mentor channel is created
"""

        if command == 'lock' or command == 'unlock':
            content = """
**!lock <channel code>** - Locks all giveaway channels with the specified code so users cannot message
**!unlock <channel code>** - Unlocks all giveaway channels with the specified code so users can message

*Note* - this toggles off or on the 'Send Messages' permission for the giveaway winners role

```
channel code:  the 4-character identifier for the channels and roles
```
"""

        if command == 'giveall':
            content = """
**!giveall <role>** - Gives all users who has posted in the channel a specified role.

*Note* - this will currently also grant you the role.

```
role:  the tag of the role to grant to message posters
```
"""

        await ctx.send(content=content)

@bot.event
async def on_command_error(ctx, error):
    err = getattr(error, "original", error)

    if isinstance(err, commands.MissingAnyRole):
        return
    if isinstance(err, commands.CommandNotFound):
        return
    if isinstance(err, discord.Forbidden):
        await ctx.send(content='I am missing permissions to do this!')
        return
    
    raise err

bot.run(bot_token)
