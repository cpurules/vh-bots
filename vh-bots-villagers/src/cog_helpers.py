import asyncio
from pyArango.theExceptions import DocumentNotFoundError, ValidationError
import bot_config
import discord

from discord.ext import commands
from embed_builder import EmbedBuilder

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

    @staticmethod
    def check_is_admin(ctx):
        if CogHelpers.bot is None:
            raise RuntimeError("Must run set_bot before using this check")
        
        user_id = ctx.message.author.id
        member = CogHelpers.get_guild_member(user_id)
        if member is None:
            return False
        
        admin_roles = []
        for role in member.roles:
            if role.id in admin_roles.value:
                return True
    
    @staticmethod
    def check_is_channel_or_dm(ctx):
        channel = ctx.channel
        command_channels = []
        return (channel.id in command_channels.value or
                isinstance(channel, discord.channel.DMChannel))
    
    @staticmethod
    def check_is_guild_member(ctx):
        if CogHelpers.bot is None:
            raise RuntimeError("Must run set_bot before using this check")
        
        user_id = ctx.message.author.id
        member = CogHelpers.get_guild_member(user_id)
        return not member is None
    
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
    def get_user_full_name(user: discord.User):
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
    def validate_is_reply(msg, in_reply_to: discord.Message, expected_author: int=None):
        return (msg.channel.id == in_reply_to.channel.id and
                not msg.author.bot and
                (expected_author is None or msg.author.id == expected_author))