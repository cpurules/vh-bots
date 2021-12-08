import asyncio
from pyArango.theExceptions import DocumentNotFoundError, ValidationError
import bot_config
import discord

from discord.ext import commands
from embed_builder import EmbedBuilder
from member import GuildMember
from redemption import Redemption
from settings import *

CONFIG = bot_config.BotConfig()

class CogHelpers(commands.Cog):
    bot = None

    CHECK_EMOJI = '\N{WHITE HEAVY CHECK MARK}'
    CANCEL_EMOJI = '\N{NEGATIVE SQUARED CROSS MARK}'
    EDIT_EMOJI = '\N{PENCIL}'
    NEXT_EMOJI = '\N{BLACK RIGHT-POINTING TRIANGLE}'
    PREV_EMOJI = '\N{BLACK LEFT-POINTING TRIANGLE}'

    @staticmethod
    def set_bot(bot):
        CogHelpers.bot = bot
        CONFIG.bot = bot
    
    @staticmethod
    def check_is_admin(ctx):
        if CogHelpers.bot is None:
            raise RuntimeError("Must run set_bot before using this check")
        
        user_id = ctx.message.author.id
        member = CONFIG.get_guild_member(user_id)
        if member is None:
            return False
        
        admin_roles = BotSettings.get_setting('admin', 'ADMIN_ROLES', int)
        for role in member.roles:
            if role.id in admin_roles.value:
                return True
    
    @staticmethod
    def check_is_channel_or_dm(ctx):
        channel = ctx.channel
        command_channels = BotSettings.get_setting('admin', 'COMMAND_CHANNELS', int)
        return (channel.id in command_channels.value or
                isinstance(channel, discord.channel.DMChannel))
    
    @staticmethod
    def check_is_guild_member(ctx):
        if CogHelpers.bot is None:
            raise RuntimeError("Must run set_bot before using this check")
        
        user_id = ctx.message.author.id
        member = CONFIG.get_guild_member(user_id)
        return not member is None
    
    @staticmethod
    def embed_membership_required():
        return EmbedBuilder().setTitle("Wait a sec...") \
                                .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value) \
                                .setDescription("You haven't joined the community bot yet!") \
                                .appendToDescription("Use `c.join` to create a profile and get started!")
    
    @staticmethod
    def get_guild():
        if CogHelpers.bot is None:
            raise RuntimeError("Must run set_bot before using this method")
        
        guild = discord.utils.get(CogHelpers.bot.guilds, id=CONFIG.GUILD_ID)
        if guild is None:
            raise RuntimeError("Bot is not a member of guild {0}".format(CONFIG.GUILD_ID))
        
        return guild
    
    @staticmethod
    def get_guild_channel_by_id(channel):
        guild = CogHelpers.get_guild()
        return discord.utils.get(guild.channels, id=channel)
    
    @staticmethod
    def get_guild_member(member):
        guild = CogHelpers.get_guild()
        return guild.get_member(member)
    
    @staticmethod
    def get_user_full_name(user):
        if user is None:
            return None
        else:
            return "{0}#{1}".format(user.name, user.discriminator)

    @staticmethod
    def intmap(obj: list):
        if not isinstance(obj, list) and not isinstance(obj, tuple):
            raise ValueError('Only works on lists and tuples')
        return [int(x) for x in obj]
    
    @staticmethod
    def parsebool(b: str):
        trues = ['yes', 'y', 'true', 'on', 'enable', 'enabled']
        falses = ['no', 'n', 'false', 'off', 'disable', 'disabled']
        if not b.lower() in (trues + falses):
            raise ValueError("Unable to parse boolean string", b)
        return b.lower() in trues
    
    @staticmethod
    async def require_bot_membership(ctx):
        if GuildMember.get_member_by_id(ctx.author.id) is None:
            await ctx.send(embed=CogHelpers.embed_membership_required().build())
            return False
        return True
    
    @staticmethod
    def validate_is_reply(msg, in_reply_to, expected_author: int=None):
        return (msg.channel.id == in_reply_to.channel.id and
                not msg.author.bot and
                (expected_author is None or msg.author.id == expected_author))
    
#        
#    
#    def get_guild_role_by_name(self, role_name):
#        guild = self.GET_GUILD()
#        return discord.utils.get(guild.roles, name=role_name)
#    
#    def get_guild_role_by_id(self, role_id):
#        guild = self.GET_GUILD()
#        return discord.utils.get(guild.roles, id=role_id)
#    
