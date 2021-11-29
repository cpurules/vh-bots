import asyncio
import bot_config
import discord
import re

from discord.ext import commands
from vh_member_game_info import VHMemberGameInfo
from vh_queue import VHQueue

CONFIG = bot_config.BotConfig()

class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.updating_queues = []
        self.restricted_role = None
    
    def can_create_queue(ctx):
        user_id = ctx.message.author.id

        member = CONFIG.get_guild_member(user_id)
        if member is None:
            return False
        
        if member.id in CONFIG.CREATE_QUEUE_USERS:
            return True

        for member_role in member.roles:
            if member_role.id in CONFIG.CREATE_QUEUE_ROLES or member_role.id == CONFIG.EVENTS_TEAM_ROLE:
                return True
        
        return False
    
    def generate_queue_roster(queue):
        queue_active_members = queue.get_active_members()

        embed_title = 'Active Visitors in Queue'
        embed_color = 0xFFFFFF
        embed_desc_lines = []

        i = 1
        for member_id in queue_active_members:
            member = CONFIG.get_guild_member(member_id)
            member_game_info = VHMemberGameInfo.get_mgi_by_user(member_id)
            embed_desc_lines.append('**{0}**. {1} - {2} from {3}'.format(i, member.mention, member_game_info.player_name, member_game_info.island_name))
            i = i + 1
        
        embed_desc = '\n'.join(embed_desc_lines)
        embed = discord.Embed(title=embed_title, color=embed_color, description=embed_desc)
        return embed
    
    def has_game_info(ctx):
        user_id = ctx.message.author.id

        member_game_info = VHMemberGameInfo.get_mgi_by_user(user_id)
        return not member_game_info is None
    
    def is_guild_member(ctx):
        user_id = ctx.message.author.id

        member = CONFIG.get_guild_member(user_id)
        return not member is None
    
    async def post_or_update_dodo(self, queue):
        channel_id = queue.channel_id
        channel = CONFIG.get_guild_text_channel(channel_id)

        island_name = queue.island_name
        dodo_code = queue.get_formatted_dodo()
        dodo_msg = 'You are currently in the queue for **{0}**\nThe current Dodo code for this island is: **{1}**\n**_This is an automated bot message - please do not remove._**'.format(island_name, dodo_code)

        messages = await channel.history(limit=1, oldest_first=True).flatten()
        if len(messages) == 0:
            msg = await channel.send(content=dodo_msg)
            await msg.pin()
        else:
            await messages[0].edit(content=dodo_msg)

            role = CONFIG.get_guild_role_by_name(queue.get_queue_name())
            await channel.send(content=('{0} - please note the dodo code has been updated to **{1}**').format(role.mention, dodo_code))
    
    async def post_or_update_roster(self, queue):
        channel_id = queue.channel_id
        channel = CONFIG.get_guild_text_channel(channel_id)

        if queue.roster_message_id is None:
            msg = await channel.send(embed=QueueCog.generate_queue_roster(queue))
            await msg.pin()
            queue.set_roster_message_id(msg.id)
        else:
            msg = await channel.fetch_message(queue.roster_message_id)
            await msg.edit(embed=QueueCog.generate_queue_roster(queue))
    
    async def post_report(self, queue, reporter, report):
        channel_id = queue.channel_id
        channel = CONFIG.get_guild_text_channel(channel_id)
        owner = CONFIG.get_guild_member(queue.owner_id)

        report_message = 'Hi {0}!  {1} reported an issue with your queue: {2}'.format(owner.mention, reporter.mention, report)
        await channel.send(content=report_message)
    
    async def process_join_or_leave(self, queue, *, kicked: bool=False):
        owner_id = queue.owner_id
        while owner_id in self.updating_queues:
            await asyncio.sleep(1)
        
        self.updating_queues.append(owner_id)

        queue_members_active = queue.get_active_members()

        queue_role = CONFIG.get_guild_role_by_name(queue.get_queue_name())
        role_members = queue_role.members
        role_members_id = [role_member.id for role_member in role_members]

        queue_channel = CONFIG.get_guild_text_channel(queue.channel_id)

        for role_member in role_members:
            if not role_member.id in queue_members_active:
                await role_member.remove_roles(queue_role)

                member_game_info = VHMemberGameInfo.get_mgi_by_user(role_member.id)
                if member_game_info is None:
                    player_name = 'N/A'
                    island_name = 'N/A'
                else:
                    player_name = member_game_info.player_name
                    island_name = member_game_info.island_name

                if not kicked:
                    await queue_channel.send(content=('{0} ({1} from {2}) has been removed from the queue channel.').format(role_member.mention, player_name, island_name))
        for queue_member_id in queue_members_active:
            if not queue_member_id in role_members_id:
                queue_member = CONFIG.get_guild_member(queue_member_id)
                await queue_member.add_roles(queue_role)

                member_game_info = VHMemberGameInfo.get_mgi_by_user(queue_member_id)
                if member_game_info is None:
                    player_name = 'N/A'
                    island_name = 'N/A'
                else:
                    player_name = member_game_info.player_name
                    island_name = member_game_info.island_name
                
                await queue_member.send(content=('Hi {0}!  It is your turn in queue {1}.  Please check out the {2} channel for more details -- your Dodo code is in the pinned messages!\n\n**If this is a treasure island** - please remember to empty your pockets before visiting!').format(queue_member.mention, queue.join_code, queue_channel.mention))
                await queue_channel.send(content=('{0} ({1} from {2}) has been added to the queue channel.').format(queue_member.mention, player_name, island_name))
        
        await self.post_or_update_roster(queue)
        self.updating_queues.remove(owner_id)
    
    async def remove_restricted_role(self, user_id):
        member = CONFIG.get_guild_member(user_id)
        await member.remove_roles(self.restricted_role)
    
    def validate_restricted_role(self, ctx):
        if self.restricted_role is None:
            return True
        
        user_id = ctx.message.author.id

        member = CONFIG.get_guild_member(user_id)
        if member is None:
            return False

        if member.id in CONFIG.CREATE_QUEUE_USERS:
            return True

        for member_role in member.roles:
            if member_role.id in CONFIG.CREATE_QUEUE_ROLES or member_role.id == self.restricted_role.id:
                return True
        
        return False

    @commands.command(name='close')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def close_queue(self, ctx):
        react_emojis = ['\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}']
        
        existing_queue = VHQueue.get_queue_by_owner(ctx.author.id)
        if existing_queue is None:
            await ctx.send(content='You do not have an active queue to close!')
            return
        
        msg = await ctx.send(content='**Are you sure you wish to close your queue?**\nNote: This will **kick** everyone out who is still in line!')
        for emoji in react_emojis:
            await msg.add_reaction(emoji)
        
        def validate_react(react, user):
            return react.emoji in react_emojis and user.id == ctx.author.id and react.message.id == msg.id
        
        try:
            react = await self.bot.wait_for('reaction_add', check=validate_react, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(content='You took to long to reply!  Your queue **has not** been closed.')
        else:
            react = react[0]
            if react.emoji == '\N{CROSS MARK}':
                await ctx.send(content='OK!  No action taken.')
            else:
                try:
                    existing_queue.close()
                except Exception as e:
                    await ctx.send(content=('Error closing your queue: ' + str(e)))
                else:
                    await ctx.send(content='Successfully closed your queue!')
        finally:
            for emoji in react_emojis:
                await msg.remove_reaction(emoji, self.bot.user)

    @commands.command(name='create')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def create_queue(self, ctx):        
        def validate_is_reply(msg):
            return msg.author.id == ctx.author.id and msg.channel == ctx.channel
        
        existing_queue = VHQueue.get_queue_by_owner(ctx.author.id)
        if not existing_queue is None:
            await ctx.send(content='You already have an active queue!  Please end it before creating a new one.')
            return

        await ctx.send(content='Enter your maximum queue length, up to 200.')

        queue_size = 0
        while queue_size == 0:
            try:
                msg = await self.bot.wait_for('message', check=validate_is_reply, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(content='Request timed out')
                return
            else:
                try:
                    new_queue_size = int(msg.content)
                    if new_queue_size <= 0 or new_queue_size > 200:
                        raise ValueError('Invalid queue size')
                    queue_size = new_queue_size
                except ValueError:
                    await ctx.send(content='Invalid queue size.  Enter your maximum queue length, up to 200.')
        await ctx.send(content='Set queue size to {0}'.format(queue_size))
        
        await ctx.send(content='Enter the maximum number of visitors at once, up to 7')

        queue_at_once = 0
        while queue_at_once == 0:
            try:
                msg = await self.bot.wait_for('message', check=validate_is_reply, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(content='Request timed out')
                return
            else:
                try:
                    new_queue_at_once = int(msg.content)
                    if new_queue_at_once <= 0 or new_queue_at_once > 7:
                        raise ValueError('Invalid visitor count')
                    queue_at_once = new_queue_at_once
                except ValueError:
                    await ctx.send(content='Invalid visitor count.  Enter the maximum number of visitors at once, up to 7')
        await ctx.send(content='Set maximum visitors at once to {0}'.format(queue_at_once))

        await ctx.send(content='Enter the Dodo code for your island.')

        dodo_code = ''
        while dodo_code == '':
            try:
                msg = await self.bot.wait_for('message', check=validate_is_reply, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(content='Request timed out')
                return
            else:
                try:
                    new_dodo_code = msg.content
                    if len(new_dodo_code) != 5:
                        raise ValueError('Invalid Dodo code')
                    dodo_code = new_dodo_code
                except ValueError:
                    await ctx.send(content='Invalid Dodo code.  Enter the Dodo code for your island.')
            dodo_code = dodo_code.upper()
        await ctx.send(content='Dodo code set to {0}'.format(dodo_code))

        await ctx.send(content='Enter the name of your island.')

        island_name = ''
        while island_name == '':
            try:
                msg = await self.bot.wait_for('message', check=validate_is_reply, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(content='Request timed out')
                return
            else:
                try:
                    new_island_name = msg.content.strip()
                    if len(new_island_name) < 1 or len(new_island_name) > 10:
                        raise ValueError('Invalid island name')
                    island_name = new_island_name
                except ValueError:
                    await ctx.send(content='Invalid island name.  Enter the name of your island.')
        await ctx.send(content='Island name set to {0}'.format(island_name))

        try:
            queue = VHQueue.create_new_queue(ctx.author.id, queue_size, queue_at_once, dodo_code, island_name, True)
        except Exception as e:
            await ctx.send(content='Unable to create queue: ' + str(e))
            return

        guild = CONFIG.GET_GUILD()
        queue_category = discord.utils.get(guild.categories, id=CONFIG.QUEUE_CATEGORY)
        queue_name = queue.get_queue_name()
        queue_role = await guild.create_role(name=queue_name)
        events_team_role = discord.utils.get(guild.roles, id=CONFIG.EVENTS_TEAM_ROLE)
        queue_perms = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, read_message_history=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True, manage_messages=True, add_reactions=True, read_message_history=True),
            events_team_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True, manage_messages=True, add_reactions=True, read_message_history=True, manage_channels=True),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True, manage_messages=True, add_reactions=True, read_message_history=True),
            queue_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=False, read_message_history=True),
        }
        
        queue_channel = await queue_category.create_text_channel(name=queue_name, overwrites=queue_perms)
        queue.set_channel_id(queue_channel.id)
        await self.post_or_update_dodo(queue)
        await self.post_or_update_roster(queue)

        await ctx.send(content=('Successfully created your queue!  Channel: {0}\nPlease note that queues are **locked** by default.'.format(queue_channel.mention)))
    
    @commands.command(name='dodo')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def update_dodo(self, ctx, dodo: str=''):
        if dodo.strip() == '':
            await ctx.send(content='You have to specify your new Dodo code!')
            return
        elif len(dodo.strip()) != 5:
            await ctx.send(content='Invalid Dodo code!')
            return
        
        owner_id = ctx.author.id
        queue = VHQueue.get_queue_by_owner(owner_id)

        if queue is None:
            await ctx.send(content='You do not have an active queue to update!')
            return
        
        queue.set_dodo(dodo)
        await self.post_or_update_dodo(queue)
        await ctx.send(content=('Successfully updated your island Dodo code to **{0}**').format(queue.get_formatted_dodo()))
    
    @commands.command(name='end')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def end_queue(self, ctx, queue_code: str=''):
        react_emojis = ['\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}']
        
        if not queue_code == '':
            user_id = ctx.author.id
            member = CONFIG.get_guild_member(user_id)
            
            is_events = False
            for role in member.roles:
                if role.id == CONFIG.EVENTS_TEAM_ROLE:
                    is_events = True
                    break
            
            if not is_events:
                await ctx.send(content='You do not have permission to end other queues!')
                return
            
            valid_code = re.search('^[a-zA-Z]{4}$', queue_code)
            if valid_code is None:
                await ctx.send(content=('`{0}` is not a valid queue ID!'.format(queue_code)))
                return

            queue = VHQueue.get_queue_by_join_code(queue_code)
            if queue is None:
                await ctx.send(content='There is no queue with this code!')
                return
            
            msg = await ctx.send(content='**Warning!** This will force close this queue, kicking out all users in line and removing the channel and role.  Are you sure you wish to proceed?')
            for emoji in react_emojis:
                await msg.add_reaction(emoji)
            
            def validate_react(react, user):
                return react.emoji in react_emojis and user.id == ctx.author.id and react.message.id == msg.id
            
            try:
                react = await self.bot.wait_for('reaction_add', check=validate_react, timeout=10)
            except asyncio.TimeoutError:
                await ctx.send(content='You took to long to reply!  No action has been taken and the queue is still open.')
            else:
                react = react[0]
                if react.emoji == '\N{CROSS MARK}':
                    await ctx.send(content='OK!  No action taken and the queue is still open.')
                else:
                    try:
                        channel_id = queue.channel_id
                        queue_channel = CONFIG.get_guild_text_channel(channel_id)
                        channel_code = queue.join_code
                        queue_role = CONFIG.get_guild_role_by_name('queue-{0}'.format(channel_code))
                        await ctx.send(content='Removing queue role...')
                        await queue_role.delete()
                        await ctx.send(content='Removing queue...')
                        queue.end()
                        await ctx.send(content='Removing channel...')
                        await queue_channel.delete()
                    except Exception as e:
                        await ctx.send(content=('Error while removing queue: ' + str(e)))
                    else:
                        await ctx.send(content='The queue has successfully been removed.')
            finally:
                for emoji in react_emojis:
                    await msg.remove_reaction(emoji, self.bot.user)
        else:
            existing_queue = VHQueue.get_queue_by_owner(ctx.author.id)
            if existing_queue is None:
                await ctx.send(content='You do not have an active queue to close!')
                return
            if len(existing_queue.get_members()) > 0:
                await ctx.send(content='You still have users in your queue!  Use q.close to kick anyone who is still in line, and q.kick to kick anyone who is up.')
                return

            try:
                channel_id = existing_queue.channel_id
                queue_channel = CONFIG.get_guild_text_channel(channel_id)
                channel_code = existing_queue.join_code
                queue_role = CONFIG.get_guild_role_by_name('queue-{0}'.format(channel_code))
                await ctx.send(content='Removing queue role...')
                await queue_role.delete()
                await ctx.send(content='Removing queue...')
                existing_queue.end()
                await ctx.send(content='Removing channel...')
                await queue_channel.delete()
            except Exception as e:
                await ctx.send(content=('Error removing your queue: ' + str(e)))
            else:
                await ctx.send(content='Successfully ended your queue. removed the queue role, and deleted your channel!')
    
    @commands.command(name='join')
    @commands.check(is_guild_member)
    @commands.dm_only()
    async def join_queue(self, ctx, join_code: str=''):
        if not self.validate_restricted_role(ctx):
            await ctx.send(content='Sorry, you do not meet the role restriction to use the queue bot right now!')
            return
        
        if not QueueCog.has_game_info(ctx):
            await ctx.send(content='Sorry, you cannot join a queue without filling out your game info!  Use `q.gameinfo` to add your island and player name.')
            return
        
        if join_code == '':
            await ctx.send(content='You have to specify the queue ID to join!')
            return

        valid_code = re.search('^[a-zA-Z]{4}$', join_code)
        if valid_code is None:
            await ctx.send(content=('`{0}` is not a valid queue ID!'.format(join_code)))
            return
        
        user_id = ctx.author.id
        if VHQueue.is_user_in_any_queue(user_id):
            await ctx.send(content='You are already in another queue!  Please leave that queue first.')
            return
        
        queue = VHQueue.get_queue_by_join_code(join_code)
        if queue is None:
            await ctx.send(content=('Queue ID `{0}` does not exist!'.format(join_code)))
            return
        
        if user_id == queue.owner_id:
            await ctx.send(content='You cannot join a queue that you own!')
            return
        
        if not queue.is_open():
            await ctx.send(content='This queue is either locked or at capacity!  Please join a different queue.')
            return

        queue.add_member(user_id)
        await ctx.send(content=('Successfully joined queue `{0}`!'.format(join_code)))
        await self.process_join_or_leave(queue)
    
    @commands.command(name='kick')
    @commands.check(can_create_queue)
    async def kick_queue_user(self, ctx, user: discord.Member=None):
        channel_id = ctx.channel.id
        queue = VHQueue.get_queue_by_channel_id(channel_id)

        if queue is None:
            await ctx.author.send(content='You tried to use q.kick in a non-queue channel!')
            await ctx.message.delete()
            return
        
        if user is None:
            await ctx.author.send(content='You have to specify the user to kick using q.kick')
            await ctx.message.delete()
            return
        
        if user.id not in queue.get_active_members():
            await ctx.author.send(content='This user is not currently up in your queue!')
            await ctx.message.delete()
            return
        
        queue.remove_member(user.id)
        await self.process_join_or_leave(queue, kicked=True)
        await ctx.send(content=('Kicked {0} from the active queue users.'.format(user.mention)))
        await ctx.message.delete()
    
    @commands.command(name='leave')
    @commands.check(is_guild_member)
    @commands.dm_only()
    async def leave_queue(self, ctx):
        user_id = ctx.author.id
        queue = VHQueue.get_queue_by_member(user_id)
        
        if queue is None:
            await ctx.send(content='You are not currently in any queues!')
            return
        
        flag_remove_role = False
        if user_id in queue.get_active_members():
            note = 'This means you have finished your trip and will be removed from the channel!'
            flag_remove_role = True
        else:
            note = 'You will forfeit your spot in line!'
        
        react_emojis = ['\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}']
        msg = await ctx.send(content=('**Are you sure you wish to leave the queue?**\nNote: {0}\nYou have 10 seconds to react, otherwise you will remain in the queue.'.format(note)))
        for emoji in react_emojis:
            await msg.add_reaction(emoji)
        
        def validate_react(react, user):
            return react.emoji in react_emojis and user.id == ctx.author.id and react.message.id == msg.id
        
        try:
            react = await self.bot.wait_for('reaction_add', check=validate_react, timeout=10)
        except asyncio.TimeoutError:
            await ctx.send(content='You took to long to reply!  You are still in the queue.')
        else:
            react = react[0]
            if react.emoji == '\N{CROSS MARK}':
                await ctx.send(content='OK!  No action taken, you are still in the queue.')
            else:
                try:
                    queue.remove_member(user_id)
                except Exception as e:
                    await ctx.send(content=('Error removing you from the queue: ' + str(e)))
                else:
                    await ctx.send(content='You have successfully left the queue.')
                    if not self.restricted_role is None and CONFIG.REMOVE_ROLE_ON_LEAVE and flag_remove_role:
                        await self.remove_restricted_role(user_id)
                    await self.process_join_or_leave(queue)
        finally:
            for emoji in react_emojis:
                await msg.remove_reaction(emoji, self.bot.user)
    
    @commands.command(name='list')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def list_queue_members(self, ctx):
        owner_id = ctx.author.id
        queue = VHQueue.get_queue_by_owner(owner_id)

        if queue is None:
            await ctx.send(content='You do not have an active queue!')
            return
        
        queue_members = queue.get_members()
        queue_size = len(queue_members)
        queue_lines = ['You currently have **{0}** users in your queue'.format(queue_size)]
        for queue_member in queue_members:
            discord_user = CONFIG.get_guild_member(queue_member)
            queue_lines.append('{0}#{1}'.format(discord_user.name, discord_user.discriminator))
        
        await ctx.send(content=('\n'.join(queue_lines)))
    
    @commands.command(name='lock')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def lock_queue(self, ctx):
        owner_id = ctx.author.id
        queue = VHQueue.get_queue_by_owner(owner_id)

        if queue is None:
            await ctx.send(content='You do not have an active queue to lock!')
            return
        elif queue.is_locked:
            await ctx.send(content='Your queue is already locked!')
            return
        
        queue.lock()
        await ctx.send(content='Your queue is now **locked** and no new members can join.')
    
    @commands.command(name='message')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def send_queue_message(self, ctx, *, message: str=''):
        message = message.strip()
        if message == '':
            await ctx.send(content='You have to specify a message to send!')
            return

        owner_id = ctx.author.id
        queue = VHQueue.get_queue_by_owner(owner_id)

        if queue is None:
            await ctx.send(content='You do not have an active queue!')
            return
        
        queue_members = queue.get_members()
        for member_id in queue_members:
            member = self.bot.get_user(member_id)
            await member.send(content=message)
            await asyncio.sleep(1)
        
        await ctx.send(content=('Sent your message to {0} queue members!').format(len(queue_members)))
    
    @commands.command(name='queues')
    @commands.check(is_guild_member)
    @commands.dm_only()
    async def list_queues(self, ctx):
        if not self.validate_restricted_role(ctx):
            await ctx.send(content='Sorry, you do not meet the role restriction to use the queue bot right now!')
            return

        queues = VHQueue.get_all_queues()

        embed_title = 'Currently Active Queues'
        if len(queues) == 0:
            embed_desc = 'No queues are currently active!'
        else:
            embed_desc_lines = []
            for queue in queues:
                if queue.owner_id == ctx.author.id:
                    queue_emoji = '\N{GLOWING STAR}'
                elif queue.has_member(ctx.author.id):
                    queue_emoji = '\N{WHITE HEAVY CHECK MARK}'
                elif queue.is_open():
                    queue_emoji = '\N{OPEN LOCK}'
                else:
                    queue_emoji = '\N{LOCK}'

                embed_desc_lines.append('{0} Queue ID: `{1}`  ({2}/{3} users)'.format(queue_emoji, queue.join_code, queue.get_queue_size(), queue.max_size))
            embed_desc = '\n'.join(embed_desc_lines)
        embed_color = 0xFFFFFF

        embed = discord.Embed(title=embed_title, description=embed_desc, color=embed_color)
        await ctx.send(embed=embed)
        await ctx.send(content="""
\N{OPEN LOCK} - this queue is open and you can get in line
\N{LOCK} - this queue is locked or at capacity
\N{WHITE HEAVY CHECK MARK} - you are in this queue
"""
        )
    
    @commands.command(name='report')
    @commands.check(is_guild_member)
    @commands.dm_only()
    async def report_queue_issue(self, ctx, *, report_message: str=''):
        user_id = ctx.author.id
        queue = VHQueue.get_queue_by_member(user_id)

        if queue is None:
            await ctx.send(content='You are not currently in a queue!')
            return
        elif not user_id in queue.get_active_members():
            await ctx.send(content='You cannot report a queue while you are in line!')
            return

        report_message = report_message.strip()

        if report_message == '':
            await ctx.send(content='You have to include a message with your report!')
            return
        
        await self.post_report(queue, ctx.author, report_message)
    
    @commands.command(name='restrict')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def restrict_queue_to_role(self, ctx, role_id: int=0):
        if role_id == 0:
            await ctx.send(content='Usage: `q.restrict <role_id>`')
            return
        
        self.restricted_role = CONFIG.get_guild_role_by_id(role_id)
        await ctx.send(content='Restricted role set to ' + self.restricted_role.name)
    
    @commands.command(name='status')
    @commands.check(is_guild_member)
    @commands.dm_only()
    async def queue_status(self, ctx):
        user_id = ctx.author.id
        queue = VHQueue.get_queue_by_member(user_id)

        if queue is None:
            await ctx.send(content='You are not currently in any queues!')
            return
        
        queue_members = queue.get_members()
        queue_length = len(queue_members)
        queue_position = queue_members.index(user_id) + 1

        await ctx.send(content=('You are currently in position **{0}**.  There are **{1}** people in line.\nThis queue allows **{2}** visitors at a time'.format(queue_position, queue_length, queue.max_at_once)))
    
    @commands.command(name='unlock')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def unlock_queue(self, ctx):
        owner_id = ctx.author.id
        queue = VHQueue.get_queue_by_owner(owner_id)

        if queue is None:
            await ctx.send(content='You do not have an active queue to unlock!')
            return
        elif not queue.is_locked:
            await ctx.send(content='Your queue is already open!')
            return

        queue.unlock()
        await ctx.send(content='Your queue is now **unlocked** and members can join if there is room.')

def setup(bot):
    bot.add_cog(QueueCog(bot))
    CONFIG.bot = bot