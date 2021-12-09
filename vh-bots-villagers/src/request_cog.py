import asyncio
import discord

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from request import Request, RequestStatus
from villager import Villager

class RequestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)
    
    @commands.command(name='help', aliases=['start'])
    @commands.dm_only()
    async def help(self, ctx):
        help_content = """
**__Welcome to the Villager Haven bot!__**
Let's get to pairing you with your favorite villager!

Pick a villager from the link below, and reply with `!villager <villager name>`
For example, to request Plucky, type `!villager Plucky`
https://animalcrossing.fandom.com/wiki/Villager_list_(New_Horizons)
"""

        await ctx.send(content=help_content)
    
    @commands.command(name='villager')
    @commands.dm_only()
    async def start_request(self, ctx, *villager_name: str):
        #TODO make this a nice embed
        if len(villager_name) == 0:
            await ctx.send(content='You need to specify a villager name to request!')
            return
        
        villager_name = ' '.join(villager_name).strip().title()
        villager = Villager.get_by_name(villager_name)
        #TODO make this a nice embed
        if villager is None:
            await ctx.send(content='{0} is not a valid villager name!  Please check the name\'s spelling.'.format(villager_name))
            return
        
        #TODO make this a nice embed
        if not Request.get_current_user_request(ctx.author.id) is None:
            await ctx.send(content='You have already submitted a villager request.')
            return
        
        Request.create_new_request(ctx.author.id, villager)

        request_content = """
**Your request for {0} has been submitted!**
Please check the Discord semi-often, as you'll be pinged when your villager is ready.

Make sure to use the `!status` command to update your availability to receive your Villager!
Repeated failures to collect your villager may result in being blocked from using the bot.
**Please note that setting your status to Available indicates that you are currently available and have an open plot!**
"""
        await ctx.send(content=request_content.format(villager_name))
    
    @commands.command(name='change')
    @commands.dm_only()
    async def change_villager(self, ctx, *villager_name: str):
        #TODO make this a nice embed
        if len(villager_name) == 0:
            await ctx.send(content='You need to specify a villager name to request!')
            return
        
        villager_name = ' '.join(villager_name).strip().title()
        villager = Villager.get_by_name(villager_name)
        if villager is None:
            await ctx.send(content='{0} is not a valid villager name!  Please check the name\'s spelling.'.format(villager_name))
            return
        
        #TODO make this a nice embed
        request = Request.get_current_user_request(ctx.author.id)
        if request is None:
            await ctx.send(content='You don\'t have an open villager request.')
            return
        
        request.change_villager(villager)
        change_content = """
**Your villager request has been changed to {0}!**
Please check the Discord semi-often, as you'll be pinged when your villager is ready.    

Make sure to use the `!status` command to update your availability to receive your Villager!
Repeated failures to collect your villager may result in being blocked from using the bot.
**Please note that setting your status to Available indicates that you are currently available and have an open plot!**
"""
        await ctx.send(content=change_content.format(villager_name))
    
    @commands.command(name='leave')
    @commands.dm_only()
    async def cancel_request(self, ctx):
        request = Request.get_current_user_request(ctx.author.id)
        if request is None:
            await ctx.send(content='You don\'t have an open villager request.')
            return
        
        request.cancel()
        leave_content = """
**You've left the queue!**
You can re-renter at any time; just DM me `!start`!
"""
        await ctx.send(content=leave_content)
    
    @commands.command(name='status')
    @commands.dm_only()
    async def toggle_availability(self, ctx):
        request = Request.get_current_user_request(ctx.author.id)
        if request is None:
            await ctx.send(content='You don\'t have an open villager request.')
            return
        
        request.toggle_availability()
        status_content = "Your availability has been changed to **{0}**.".format(request.status.name.title())
        if request.status == RequestStatus.AVAILABLE:
            status_content += '\n'
            status_content += 'Please note that this means you are **available, with an open plot**!'
        
        await ctx.send(content=status_content)


def setup(bot):
    bot.add_cog(RequestCog(bot))