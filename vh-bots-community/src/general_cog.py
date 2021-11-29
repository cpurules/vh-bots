import asyncio
import discord

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from settings import *

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)


def setup(bot):
    bot.add_cog(GeneralCog(bot))