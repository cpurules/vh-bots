import asyncio
import discord
import math
import random
import time

from config import BotConfig
from discord.ext import commands
from database import Database
from drawing import Drawing, DrawingType

CONFIG = BotConfig()
DB = Database()
ACTIVE_DRAWINGS = []

class DrawingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.special_team_role_id = None
        self.separate_cit_channel = CONFIG.SEPARATE_CIT_CHANNEL

        ACTIVE_DRAWINGS = Drawing.get_all_active_drawings()
        for drawing in ACTIVE_DRAWINGS:
            asyncio.ensure_future(self.run_drawing(drawing))

    @staticmethod
    def __parse_type_arg(drawing_type: str):
        return DrawingType.from_str(drawing_type)

    @staticmethod
    def __parse_winners_arg(winners: str):
        if not winners[-1] == 'w':
            raise ValueError('Bad winners format')
        
        return int(winners[0:-1])
    
    @staticmethod
    def __parse_duration_arg(duration: str):
        if not duration[-1] in ['s', 'm', 'h', 'd']:
            raise ValueError('Bad duration format')

        duration_int = int(duration[0:-1])
        duration_format = duration[-1]
        
        if duration_format == 's':
            duration_secs = duration_int
        elif duration_format == 'm':
            duration_secs = duration_int * 60
        elif duration_format == 'h':
            duration_secs = duration_int * 60 * 60
        elif duration_format == 'd':
            duration_secs = duration_int * 60 * 60 * 24
        
        return duration_secs
    
    @commands.command(name='getcitchannel')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def get_cit_channel_setting(self, ctx):
        channel_setting = 'will' if self.separate_cit_channel else 'will not'
        await ctx.send('Separate channel for CIT/Courier Mentors: **{0}** be generated.'.format(channel_setting))
    
    @commands.command(name='togglecitchannel')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def toggle_cit_channel_setting(self, ctx):
        self.separate_cit_channel = not self.separate_cit_channel
        channel_setting = 'True' if self.separate_cit_channel else 'False'
        await ctx.send('Separate channel for CIT/Courier Mentors: Set to **{0}**'.format(channel_setting))
    
    @commands.command(name='getspecial')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def get_special_role(self, ctx):
        if self.special_team_role_id is None:
            await ctx.send('No special team role set!')
        else:
            special_role = discord.utils.get(ctx.guild.roles, id=self.special_team_role_id)
            await ctx.send('Current special team role: ' + special_role.mention)
    
    @commands.command(name='setspecial')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def set_special_role(self, ctx, role: discord.Role=None):
        if role is None:
            await ctx.send('Usage: !setspecial <role>')
            return
        
        self.special_team_role_id = role.id
        await ctx.send('Set special team role to ' + role.mention)
    
    @commands.command(name='clearspecial')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def clear_special_role(self, ctx):
        self.special_team_role_id = None
        await ctx.send('Cleared special team role!')

    @commands.command(name='giveaway')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def start_giveaway(self, ctx, *, prize: str=''):
        if ''.join(prize).strip() == '':
            await ctx.send('Usage: !giveaway <prize>')
            return
        
        print('Starting a standard giveaway')
        await ctx.invoke(self.bot.get_command('drawing'), drawing_type='giveaway', winners='200w', duration='24h', claim_duration='24h', prize=prize)
    
    @commands.command(name='drawing2')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def start_special_drawing(self, ctx, drawing_type: str='', winners: str='', duration: str='', claim_duration: str='', *, prize: str=''):
        if drawing_type == '' or winners == '' or duration == '' or prize == '':
            await ctx.send('Usage: !drawing2 <type> <winners>w <duration>[s/m/h/d] <time to claim>[s/m/h/d] <prize>')
            return

        if self.special_team_role_id is None:
            await ctx.send('No special team role is set!  Please use **!setspecial** before using **!drawing2**')
            return
        
        try:
            drawing_type = DrawingCog.__parse_type_arg(drawing_type)
        except Exception:
            await ctx.send('Invalid drawing type.  Expected: giveaway/event')
            return

        try:
            winners = DrawingCog.__parse_winners_arg(winners)
        except Exception:
            await ctx.send('Invalid winners format.  Expected: ###w')
            return
        
        try:
            duration_secs = DrawingCog.__parse_duration_arg(duration)
        except Exception:
            await ctx.send('Invalid duration format.  Expected: ###[s/m/h/d]')
            return
        
        try:
            claim_duration_secs = DrawingCog.__parse_duration_arg(claim_duration)
        except Exception:
            await ctx.send('Invalid claim duration format.  Expected: ###[s/m/h/d]')
            return
        
        prize = ''.join(prize).strip()
        if prize == '':
            await ctx.send('You have to specify a prize.')
            return
        
        print('Creating a special team drawing.  Winners: {0}\tDuration (s): {1}\tPrize: {2}'.format(winners, duration_secs, prize))

        await ctx.message.delete()

        drawing = Drawing(int(time.time()), winners, duration_secs, claim_duration_secs, prize, drawing_type, True)
        
        drawing_msg = await ctx.send(embed=drawing.generate_embed())
        drawing.set_ids(drawing_msg)
        drawing.create_in_db()
        ACTIVE_DRAWINGS.append(drawing)

        await drawing.msg.add_reaction('\N{PARTY POPPER}')
        
        asyncio.ensure_future(self.run_drawing(drawing))

    @commands.command(name='drawing')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def start_drawing(self, ctx, drawing_type: str='', winners: str='', duration: str='', claim_duration: str='', *, prize: str=''):
        if drawing_type == '' or winners == '' or duration == '' or prize == '':
            await ctx.send('Usage: !drawing <type> <winners>w <duration>[s/m/h/d] <time to claim>[s/m/h/d] <prize>')
            return

        try:
            drawing_type = DrawingCog.__parse_type_arg(drawing_type)
        except Exception:
            await ctx.send('Invalid drawing type.  Expected: giveaway/event')
            return

        try:
            winners = DrawingCog.__parse_winners_arg(winners)
        except Exception:
            await ctx.send('Invalid winners format.  Expected: ###w')
            return
        
        try:
            duration_secs = DrawingCog.__parse_duration_arg(duration)
        except Exception:
            await ctx.send('Invalid duration format.  Expected: ###[s/m/h/d]')
            return
        
        try:
            claim_duration_secs = DrawingCog.__parse_duration_arg(claim_duration)
        except Exception:
            await ctx.send('Invalid claim duration format.  Expected: ###[s/m/h/d]')
            return
        
        prize = ''.join(prize).strip()
        if prize == '':
            await ctx.send('You have to specify a prize.')
            return
        
        print('Creating a drawing.  Winners: {0}\tDuration (s): {1}\tPrize: {2}'.format(winners, duration_secs, prize))

        await ctx.message.delete()

        drawing = Drawing(int(time.time()), winners, duration_secs, claim_duration_secs, prize, drawing_type, False)
        
        drawing_msg = await ctx.send(embed=drawing.generate_embed())
        drawing.set_ids(drawing_msg)
        drawing.create_in_db()
        ACTIVE_DRAWINGS.append(drawing)

        await drawing_msg.add_reaction('\N{PARTY POPPER}')

        asyncio.ensure_future(self.run_drawing(drawing))
    
    async def run_drawing(self, drawing):
        msg_channel = CONFIG.get_guild_text_channel(drawing.channel_id)
        if msg_channel is None:
            return
        msg = await msg_channel.fetch_message(drawing.message_id)
        if msg is None:
            return

        while not drawing.is_ended():
            await msg.edit(embed=drawing.generate_embed())
            await asyncio.sleep(drawing.time_to_next_update())
        
        print('Drawing for {0} has ended'.format(drawing.prize))
        await msg.edit(embed=drawing.generate_embed())

        winners = await self.select_winners(drawing)

        if len(winners) == 0:
            await msg_channel.send(content='Oops!  Nobody won this drawing :(')
            return
        
        return
        #await self.announce_winners(drawing, winners)
        #await self.process_winners(drawing, winners)
    
    async def select_winners(self, drawing):
        msg_channel = CONFIG.get_guild_text_channel(drawing.channel_id)
        drawing_msg = await msg_channel.fetch_message(drawing.message_id)

        reactions = drawing_msg.reactions
        for reaction in reactions:
            if not reaction.emoji == '\N{PARTY POPPER}':
                continue
            
            # Get all non-bot, still-member entrants
            entrants = await reaction.users().flatten()
            entrants = list(filter(lambda x: not x.bot and type(x) is discord.Member, entrants))
            break
        
        random.shuffle(entrants)
        winners = []
        while len(winners) < drawing.winners and len(entrants) > 0:
            winners.append(entrants.pop())
        
        return winners
    
    async def announce_winners(self, drawing, winners):
        ctx = await self.bot.get_context(drawing.msg)
        guild = ctx.guild

        all_winner_mentions = []
        current_winner = 0
        for winner in winners:
            current_winner_post = int(current_winner / CONFIG.MAX_WINNERS_PER_POST)
            if current_winner % CONFIG.MAX_WINNERS_PER_POST == 0:
                all_winner_mentions.append([])
            all_winner_mentions[current_winner_post].append(winner.mention)
            current_winner += 1
        
        for winner_mentions in all_winner_mentions:
            await ctx.send(content='Congratulations to our {0} winners! {1}'.format(drawing.prize, " ".join(winner_mentions)))
        
        if drawing.drawing_type == DrawingType.GIVEAWAY:
            pitfall_emoji = await guild.fetch_emoji(CONFIG.PITFALL_EMOJI)
            events_team_role = guild.get_role(CONFIG.EVENTS_TEAM_ROLE)
            await ctx.send(content=generate_giveaway_instructions(pitfall_emoji, events_team_role))

    async def process_winners(self, drawing, winners):
        ctx = await self.bot.get_context(drawing.msg)
        guild = ctx.guild
        
        if drawing.drawing_type == DrawingType.GIVEAWAY:
            max_per_group = CONFIG.MAX_WINNERS_PER_GIVEAWAY_GROUP
        elif drawing.drawing_type == DrawingType.EVENT:
            max_per_group = CONFIG.MAX_WINNERS_PER_EVENT_GROUP
        else:
            raise ValueError('Drawing is of an unknown type')

        group_count = math.ceil(len(winners) / max_per_group)

        while True:
            giveaway_id = ''.join(chr(x) for x in random.sample(range(ord('a'), ord('f')+1), 4))
            test_role_name = 'winners-{0}-1'.format(giveaway_id)
            if discord.utils.get(guild.roles, name=test_role_name) is None and not giveaway_id in ['deaf', 'dead', 'caca']:
                break
        
        if drawing.drawing_type == DrawingType.GIVEAWAY:
            channel_category_id = CONFIG.GIVEAWAY_CATEGORY
            role_type = 'giveaway'
        elif drawing.drawing_type == DrawingType.EVENT:
            channel_category_id = CONFIG.EVENT_CATEGORY
            role_type = 'event'
        
        channel_category = discord.utils.get(guild.categories, id=channel_category_id)
        logging_channel = discord.utils.get(guild.text_channels, id=CONFIG.LOGGING_CHANNEL)
        events_team_role = guild.get_role(CONFIG.EVENTS_TEAM_ROLE)
        cit_role = guild.get_role(CONFIG.CIT_ROLE)
        mentor_role = guild.get_role(CONFIG.COURIER_MENTOR_ROLE)
        pitfall_emoji = await guild.fetch_emoji(CONFIG.PITFALL_EMOJI)
        
        channel_perms_template = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, add_reactions=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True, external_emojis=True, manage_messages=True, add_reactions=True),
            events_team_role: discord.PermissionOverwrite(manage_channels=True, manage_permissions=True, read_messages=True, send_messages=True, mention_everyone=True, manage_messages=True)
        }

        channel_role_perms = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True, add_reactions=False, external_emojis=False)
        channel_role_perms_couriers = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True, add_reactions=True, external_emojis=False)

        for i in range(0, group_count):
            winners_in_group = 0
            role_name = '{0}-{1}-{2}'.format(role_type, giveaway_id, i + 1)
            print('Creating role ' + role_name)
            channel_role = await guild.create_role(name=role_name)

            while len(winners) > 0 and winners_in_group < max_per_group:
                winner = winners.pop()
                print('Assigning role {0} to {1}'.format(role_name, winner.name))
                await winner.add_roles(channel_role, reason="Giveaway winner", atomic=True)
                await asyncio.sleep(1)
                winner = guild.get_member(winner.id)
                if channel_role in winner.roles:
                    await logging_channel.send(content='Gave {0} the {1} role'.format(winner.mention, channel_role.name))
                else:
                    await logging_channel.send(content='Failed to give {0} the {1} role'.format(winner.mention, channel_role.name))
                winners_in_group += 1
            
            channel_name = 'winners-{0}-{1}'.format(giveaway_id, i + 1)
            
            channel_perms = dict(channel_perms_template)
            channel_perms[channel_role] = channel_role_perms
            mention_roles = []
            if drawing.is_special:
                special_role = guild.get_role(self.special_team_role_id)
                channel_perms[special_role] = channel_role_perms_couriers
                mention_roles.append(special_role)
            elif drawing.drawing_type == DrawingType.GIVEAWAY:
                # Giveaways have special rules for who is added to the channels (changed 12/29 for CITs/Courier Mentors)
                # If SEPARATE_CIT_CHANNEL is ON:
                # --> if this is the LAST channel, only add CITs and Courier Mentors
                # --> if this is NOT the LAST channel, then add Couriers and Suppliers
                # If SEPARATE_CIT_CHANNEL is OFF, **OR** there is only one channel to create:
                # --> add Couriers, CITs, Suppliers to all channels
                supplier_role = guild.get_role(CONFIG.SUPPLIER_ROLE)
                
                if not self.separate_cit_channel or group_count == 1:
                    channel_perms[supplier_role] = channel_role_perms_couriers
                    for courier_role_id in CONFIG.COURIER_ROLES:
                        courier_role = guild.get_role(courier_role_id)
                        if not courier_role is None:
                            channel_perms[courier_role] = channel_role_perms_couriers
                            mention_roles.append(courier_role)
                else:
                    if i == (group_count - 1):
                        courier_roles = [cit_role, mentor_role]
                        mention_roles = [cit_role, mentor_role]
                    else:
                        courier_role_ids = [id for id in CONFIG.COURIER_ROLES if not id == cit_role.id]
                        courier_roles = [guild.get_role(courier_role_id) for courier_role_id in courier_role_ids]
                        mention_roles = list(courier_roles)
                        courier_roles.append(supplier_role)
                    for courier_role in courier_roles:
                        channel_perms[courier_role] = channel_role_perms_couriers

            print('Creating channel ' + channel_name)
            channel = await guild.create_text_channel(name=channel_name, overwrites=channel_perms, category=channel_category)

            print('Sending congratulations message to channel')
            if drawing.drawing_type == DrawingType.GIVEAWAY:
                await channel.send(generate_giveaway_message(mention_roles, channel_role, drawing.prize, pitfall_emoji, events_team_role, drawing.claim_duration))
            elif drawing.drawing_type == DrawingType.EVENT:
                await channel.send(generate_event_message(channel_role, drawing.prize, events_team_role))
        
        print('Done!')
    
    @commands.command(name='remind')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def remind_and_clean(self, ctx, time_left: str=''):
        if time_left == '':
            await ctx.send(content='Usage: !remind <time left>')
            return
        
        try:
            time_left = DrawingCog.__parse_duration_arg(time_left)
            if time_left <= 0:
                raise Exception('Need a positive time')
        except Exception:
            await ctx.send('Invalid remaining time.  Expected: ###[d/h/m/s]')
            return

        giveaway_channel = ctx.channel

        if not giveaway_channel.name.startswith('winners-'):
            return

        role_identifier = giveaway_channel.name.split('-', 1)[1]
        role_name = 'giveaway-' + role_identifier
        channel_role = discord.utils.get(ctx.guild.roles, name=role_name)

        # clean roles
        async for message in giveaway_channel.history(limit=CONFIG.MAX_WINNERS_PER_GIVEAWAY_GROUP*2):
            if message.author.bot or not type(message.author) is discord.Member:
                continue
            
            reactions = message.reactions
            msg_is_checked = False
            msg_is_xed = False
            is_processed = False

            for reaction in reactions:
                if reaction.emoji == '\N{WHITE HEAVY CHECK MARK}':
                    msg_is_checked = True
                elif reaction.emoji == '\N{CROSS MARK}':
                    msg_is_xed = True
                elif reaction.emoji == '\N{BALLOT BOX WITH CHECK}':
                    is_processed = True
                    break
            
            if is_processed:
                continue

            if msg_is_checked and msg_is_xed:
                # Remove role
                await message.author.remove_roles(channel_role)

                # Add emoji to mark as processed
                await message.add_reaction('\N{BALLOT BOX WITH CHECK}')
        
        pitfall_emoji = await ctx.guild.fetch_emoji(CONFIG.PITFALL_EMOJI)
        events_team_role = ctx.guild.get_role(CONFIG.EVENTS_TEAM_ROLE)

        await ctx.channel.send(content=generate_reminder_message(channel_role, pitfall_emoji, events_team_role, time_left))
        
        await ctx.message.delete()

def generate_reminder_message(channel_role, pitfall_emoji, events_team_role, time_left):
    content = """{0}

\N{PARTY POPPER} **__REMINDER WINNERS!__** \N{PARTY POPPER}

*Here is where you will be able to collect your giveaway prize.  Please post when you are **Ready** and able to collect.  A staff member will get to you when they can...*

\N{SMALL ORANGE DIAMOND} *Please prepare a **DODO** code.*
\N{SMALL ORANGE DIAMOND} *After you have a **DODO** code, post **Ready** in the channel.  A courier will message you. Please have DM's on.*
\N{SMALL ORANGE DIAMOND} *Once you are helped you will be removed from the channel.*
{1} **__DO NOT__** *post anything other than **Ready** in the channel.*
{1} **__DO NOT__** *react to messages as it messes with our delivery system.*
{1} **If you cannot claim your prize** - no worries!  Feel free to either send a friend's Dodo, or DM a member of the {2} to be removed from the channel.

> *If you have any questions or concerns, please contact a member of the* {2}

 __**You have {3} left to redeem your prize.**__
 """
    return content.format(channel_role.mention, str(pitfall_emoji), events_team_role.mention, Drawing.format_duration(time_left))
    
def generate_giveaway_message(mention_roles, channel_role, prize, pitfall_emoji, events_team_role, claim_duration):
    content = """{0}
    
{1}
    
\N{PARTY POPPER} **__Congratulations Winners!__** \N{PARTY POPPER}
*Here is where you will be able to collect your prize of **__{2}__**. Please post when you are **Ready** and able to collect. A staff member will get to you when they can...*

\N{SMALL ORANGE DIAMOND} *Please prepare a **DODO** code.*
\N{SMALL ORANGE DIAMOND} *After you have a **DODO** code, post **Ready** in the channel.  A courier will message you. Please have DM's on.*
\N{SMALL ORANGE DIAMOND} *Once you are helped you will be removed from the channel.*
{3} **__DO NOT__** *post anything other than **Ready** in the channel.*
{3} **__DO NOT__** *react to messages as it messes with our delivery system.*
{3} **If you cannot claim your prize** - no worries!  Feel free to either send a friend's Dodo, or DM a member of the {4} to be removed from the channel.

> *If you have any questions or concerns, please contact a member of the* {4}

 __**You have {5} to redeem your prize.**__
 """
    role_mentions = " ".join([mention_role.mention for mention_role in mention_roles])
    return content.format(role_mentions, channel_role.mention, prize, str(pitfall_emoji), events_team_role.mention, Drawing.format_duration(claim_duration))

def generate_event_message(channel_role, prize, events_team_role):
    content = """{0}

\N{PARTY POPPER} **__Congratulations Winners!__** \N{PARTY POPPER}
*Here is where you will be able to find more information about your prize of **__{1}__**.  A member of the **__{2}__** will post here shortly with more details.*
"""
    return content.format(channel_role.mention, prize, events_team_role.mention)

def generate_giveaway_instructions(pitfall_emoji, events_team_role):
    content = """\N{PARTY POPPER} **__I won a GIVEAWAY!  What do I do?__** \N{PARTY POPPER}
    
\N{SMALL ORANGE DIAMOND} Winners will be assigned a giveaway role - *this will allow access into a private channel*
\N{SMALL ORANGE DIAMOND} Giveaway winners will prepare a DODO code and then post *"Ready"* in the private channel
\N{SMALL ORANGE DIAMOND} A Courier will DM each "Ready" winner to deliver the prize(s)
{0} **If you do not get assigned a winner role after 1 hour, please contact a member of the {1}**
{0} **If you cannot claim your prize** - no worries!  Feel free to either send a friend's Dodo, or DM a member of the {1} to be removed from the channel.
"""
    return content.format(str(pitfall_emoji), events_team_role.mention)

def setup(bot):
    bot.add_cog(DrawingCog(bot))
    CONFIG.bot = bot