import asyncio
import discord

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from villager import Villager

class RequestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)
    
    @commands.command(name='help', aliases=['start'])
    @commands.dm_only()
    async def help(self, ctx):
        content = """
**Welcome to the Villager Haven bot!**
Let's get to pairing you with your favorite villager!

Pick a villager name from the link below, and reply with `!villager <villager name>`, without the brackets.
For example, to request Plucky, type `!villager Plucky`
https://animalcrossing.fandom.com/wiki/Villager_list_(New_Horizons)
"""
        await ctx.send(content=content)