import asyncio
import discord

from config import BotConfig
from discord.ext import commands
from drawing import DrawingType

CONFIG = BotConfig()

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='announce')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def announce_giveaway(self, ctx, prize: str=None):
        if prize is None or prize == '':
            return
        
        channel = discord.utils.get(ctx.guild.text_channels, id=CONFIG.GIVEAWAY_CHAT_CHANNEL)
        await channel.send(content=generate_giveaway_internal_announce(prize))
    
    @commands.command(name='giveall')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def give_all_role(self, ctx, role: discord.Role=None):
        if role is None:
            await ctx.send('Usage: !giveall <role>')
            return
        
        logging_channel = discord.utils.get(ctx.guild.text_channels, id=CONFIG.LOGGING_CHANNEL)
        granted_to = []

        async for message in ctx.channel.history(limit=None):
            author = message.author
            if author in granted_to:
                continue
            await author.add_roles(role, atomic=True)
            await asyncio.sleep(1)

            author = ctx.guild.get_member(author.id)
            if role in author.roles:
                await logging_channel.send(content='Gave {0} the {1} role'.format(author.mention, role.name))
                granted_to.append(author)
            else:
                await logging_channel.send(content='Failed to give {0} the {1} role {2}'.format(author.mention, role.name, ctx.author.mention))
        
        await ctx.channel.send(content='Granted role {0} to all users who posted in channel'.format(role.name))

    @commands.command(name='channel')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def create_blank_channel(self, ctx, channel_type: str='', channel_count: int=1):
        if channel_type == '':
            await ctx.send('Usage: !channel <type> [<count=1>]')
            return
        
        try:
            channel_type = DrawingType.from_str(channel_type)
        except Exception:
            await ctx.send('Invalid channel type.  Expected: giveaway/event')
            return

        try:
            channel_count = int(channel_count)
            if channel_count < 1:
                raise Exception('Bad channel count')
        except Exception:
            await ctx.send('Invalid channel count.  Expected: ###')
            return
        
        channel_type_name = channel_type.name.lower()
        
        print('Creating {0} {1} channel(s)'.format(channel_count, channel_type_name))

        guild = ctx.guild

        channel_perms_template = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, add_reactions=False),
        }

        events_team_role = guild.get_role(CONFIG.EVENTS_TEAM_ROLE)
        events_team_perms = discord.PermissionOverwrite(manage_channels=True, manage_permissions=True, read_messages=True, send_messages=True, mention_everyone=True, manage_messages=True, add_reactions=True)
        channel_perms_template[events_team_role] = events_team_perms

        if channel_type == DrawingType.GIVEAWAY:
            channel_category_id = CONFIG.GIVEAWAY_CATEGORY
            courier_role_perms = discord.PermissionOverwrite(add_reactions=True)

            for courier_role_id in CONFIG.COURIER_ROLES:
                courier_role = guild.get_role(courier_role_id)
                channel_perms_template[courier_role] = courier_role_perms
                
        elif channel_type == DrawingType.EVENT:
            channel_category_id = CONFIG.EVENT_CATEGORY
        
        channel_category = discord.utils.get(guild.categories, id=channel_category_id)

        channel_mentions = []
        for i in range(0, channel_count):
            channel_perms = dict(channel_perms_template)
            channel_name = 'blank-{0}-{1}'.format(channel_type_name, (i + 1))
            channel = await guild.create_text_channel(name=channel_name, overwrites=channel_perms, category=channel_category)
            channel_mentions.append(channel.mention)
        
        await ctx.message.delete()

        msg = 'Created {0} channels: {1}'.format(channel_count, ' '.join(channel_mentions))
        await ctx.channel.send(content=msg)
    
    @commands.command(name='cleanroles')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def clean_roles(self, ctx, to_clean: str=''):
        roles = ctx.guild.roles
        deleted = 0
        for role in roles:
            if role.name.startswith('event-' + to_clean) or role.name.startswith('giveaway-' + to_clean):
                print('Deleting role {0}'.format(role.name))
                await role.delete()
                deleted += 1

        if not ctx.command.name == "cleanall":
            await ctx.message.delete()

        await ctx.channel.send(content='Deleted {0} roles'.format(deleted))
        
    @commands.command(name='cleanchannels')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def clean_channels(self, ctx, to_clean: str=''):
        channels = ctx.guild.text_channels
        deleted = 0
        for channel in channels:
            if channel.name.startswith('winners-' + to_clean):
                print('Deleting channel {0}'.format(channel.name))
                await channel.delete()
                deleted += 1

        if not ctx.command.name == "cleanall":
            await ctx.message.delete()
            
        await ctx.channel.send(content='Deleted {0} channels'.format(deleted))
    
    @commands.command(name='cleanteams')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def clean_team_channels(self, ctx):
        channels = ctx.guild.text_channels
        deleted = 0
        for channel in channels:
            if channel.name.startswith('team-') or channel.name[1:].startswith('team-'):
                print('Deleting channel {0}'.format(channel.name))
                await channel.delete()
                deleted += 1
        
        await ctx.message.delete()
        await ctx.channel.send(content='Deleted {0} channels'.format(deleted))

    @commands.command(name='cleanall')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def clean_channels_and_roles(self, ctx, to_clean: str=''):
        await ctx.invoke(self.bot.get_command('cleanroles'), to_clean=to_clean)
        await ctx.invoke(self.bot.get_command('cleanchannels'), to_clean=to_clean)
        await ctx.message.delete()
    
    @commands.command(name='createteam')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def create_team_channels(self, ctx, team_name: str='', *members: discord.Member):
        if team_name == '' or len(members) == 0:
            await ctx.send(content='Usage: !createteam <team name> <member> <member> ...')
            return
        
        supplier_role = discord.utils.get(ctx.guild.roles, id=CONFIG.SUPPLIER_ROLE)
        courier_roles = []
        for courier_role_id in CONFIG.COURIER_ROLES:
            courier_role = discord.utils.get(ctx.guild.roles, id=courier_role_id)
            if not courier_role is None:
                courier_roles.append(courier_role)
        
        suppliers = []
        couriers = []
        for team_member in members:
            if supplier_role in team_member.roles:
                suppliers.append(team_member)
            else:
                member_courier_roles = set(courier_roles) & set(team_member.roles)
                if len(member_courier_roles) == 0:
                    await ctx.send('{0} does not appear to be a courier or supplier!'.format(team_member.name))
                    return
                else:
                    couriers.append(team_member)
        
        if len(suppliers) == 0:
            await ctx.send('You have to add at least one supplier to the team.')
            return
        if len(couriers) == 0:
            await ctx.send('You have to add at least one courier or CIT to the team.')
            return

        events_team_role = ctx.guild.get_role(CONFIG.EVENTS_TEAM_ROLE)
        events_team_perms = discord.PermissionOverwrite(manage_channels=True, manage_permissions=True, read_messages=True, send_messages=True, mention_everyone=True, manage_messages=True, add_reactions=True)
        supplier_perms = discord.PermissionOverwrite(read_messages=True, send_messages=True, mention_everyone=True, manage_messages=True, read_message_history=True, add_reactions=True)
        courier_perms = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)

        # Set up permissions
        channel_perms = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, add_reactions=False),
            ctx.me: events_team_perms,
            events_team_role: events_team_perms,
        }

        for supplier in suppliers:
            channel_perms[supplier] = supplier_perms
        
        for courier in couriers:
            channel_perms[courier] = courier_perms
        
        giveaway_category = discord.utils.get(ctx.guild.categories, id=CONFIG.GIVEAWAY_CATEGORY)
        channel_name = 'team-{0}'.format(team_name)

        channel = await ctx.guild.create_text_channel(name=channel_name, overwrites=channel_perms, category=giveaway_category)

        embed_title = 'Giveaway Team Created!'
        embed_desc = """
{0}

**Suppliers**
{1}

**Couriers**
{2}
"""

        supplier_mentions_text = '\n'.join([supplier.mention for supplier in suppliers])
        courier_mentions_text = '\n'.join([courier.mention for courier in couriers])
        embed_color = 0xEBAE34

        embed = discord.Embed(title=embed_title, description=embed_desc.format(channel.mention, supplier_mentions_text, courier_mentions_text), color=embed_color)
        await ctx.send(embed=embed)

        pitfall_emoji = await ctx.guild.fetch_emoji(CONFIG.PITFALL_EMOJI)
        fauna_emoji = await ctx.guild.fetch_emoji(CONFIG.FAUNA_WAVE_EMOJI)
        giveaway_chat_channel = discord.utils.get(ctx.guild.text_channels, id=CONFIG.GIVEAWAY_CHAT_CHANNEL)
        intro_message = generate_team_intro(suppliers, courier_roles, team_name, fauna_emoji, giveaway_chat_channel, pitfall_emoji, events_team_role)
        await channel.send(content=intro_message)

        await ctx.message.delete()
    
    @commands.command(name='lock')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def lock_winner_channels(self, ctx, code: str=''):
        code = code.strip()
        if code == '':
            await ctx.send(content='You have to specify the giveaway channel code to lock!')
            return
        if len(code) != 4:
            await ctx.send(content='The giveaway channel code has to be 4 characters!')
            return
        
        channels = [channel for channel in ctx.guild.text_channels if channel.name.startswith('winners-{0}'.format(code))]
        for channel in channels:
            channel_num = channel.name.split('-')[-1]
            role_name = 'giveaway-{0}-{1}'.format(code, channel_num)
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            overwrites = channel.overwrites_for(role)
            overwrites.update(send_messages=False)
            await channel.set_permissions(role, overwrite=overwrites)
            await channel.send(content='**Note** - this channel has been locked, and messages cannot currently be sent.')
            await ctx.send(content=('Removed send messages from {0} in {1}'.format(role_name, channel.name)))
    
    @commands.command(name='unlock')
    async def unlock_winner_channels(self, ctx, code: str=''):
        code = code.strip()
        if code == '':
            await ctx.send(content='You have to specify the giveaway channel code to unlock!')
            return
        if len(code) != 4:
            await ctx.send(content='The giveaway channel code has to be 4 characters!')
            return
        
        channels = [channel for channel in ctx.guild.text_channels if channel.name.startswith('winners-{0}'.format(code))]
        for channel in channels:
            channel_num = channel.name.split('-')[-1]
            role_name = 'giveaway-{0}-{1}'.format(code, channel_num)
            role = discord.utils.get(ctx.guild.roles, name=role_name)

            overwrites = channel.overwrites_for(role)
            overwrites.update(send_messages=True)
            await channel.set_permissions(role, overwrite=overwrites)
            await channel.send(content='**Note** - this channel has been unlocked and is now open for messages.')
            await ctx.send(content=('Granted send messages to {0} in {1}'.format(role_name, channel.name)))

def generate_team_intro(suppliers, courier_roles, team_name, fauna_emoji, giveaway_chat_channel, pitfall_emoji, events_team_role):
    content = """
{0} {1}

Welcome Team {2}! {3}

This will be your supply team for the upcoming giveaway.  Check out {4} for more information, e.g. what items are being delivered.

> \N{SMALL ORANGE DIAMOND} Your supplier will coordinate times for pickup and will post a Dodo code and any additional information needed
> \N{SMALL ORANGE DIAMOND} Please arrive with empty pockets, and make 2-3 trips, collecting full inventories
> \N{SMALL ORANGE DIAMOND} Once you pick up your giveaway supplies, please feel free to take one inventory for yourself!
> \N{SMALL ORANGE DIAMOND} **Remember to mark your inventories off in {4}!**
> {5} **If this giveaway includes DIYs, please learn them yourself first before picking up inventory for delivery!**

*If you have any questions or concerns, please ping the {6}*
"""
    supplier_mentions = ' '.join([supplier.mention for supplier in suppliers])
    courier_role_mentions = ' '.join([courier_role.mention for courier_role in courier_roles])
    team_names = team_name.split('-')
    team_name = ' / '.join([name.capitalize() for name in team_names])

    return content.format(supplier_mentions, courier_role_mentions, team_name, str(fauna_emoji),
                          giveaway_chat_channel.mention, str(pitfall_emoji), events_team_role.mention)

def generate_giveaway_internal_announce(prize: str):
    team_reacts = [
        "\N{LARGE BLUE DIAMOND}",
        "\N{LARGE ORANGE DIAMOND}",
        "\N{YELLOW HEART}",
        "\N{HEAVY BLACK HEART}",
        "\N{LARGE GREEN CIRCLE}",
        "\N{LARGE PURPLE CIRCLE}",
        "\N{GLOWING STAR}",
        "\N{CROSS MARK}"
    ]
    content = """
Hi {0} & {1} & {2}!

Tomorrow's giveaway will be for {3}

**__Couriers__** - Please react {4} for picking up this evening, or {5} for tomorrow.
**__Couriers in Training__** - Please react {6} for picking up this evening, or {7} for tomorrow.
**__Giveaway Suppliers__** - Please react {8} for supplying this evening, or {9} for tomorrow.
__Please react {10} if you don't need to pick up / are able to supply for yourself!__

Please react {11} if you will not be availablet o support this giveaway.

If you do not react at all, we will flag this!  It's okay to not participate in every giveaway, but we do need a response {12}

**Note:** Our team will set up supplier/courier teams once we have an idea of how many people are participating!
"""

    return content.format("mention1", "mention2", "mention3", prize, *team_reacts, "rosie")


def setup(bot):
    bot.add_cog(AdminCog(bot))