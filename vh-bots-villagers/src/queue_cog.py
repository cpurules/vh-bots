import asyncio
import discord

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from request import Request, RequestStatus
from villager import Villager

class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)
    
    @commands.command(name='requests')
    @commands.dm_only()
    async def show_queue(self, ctx, *list_args):
        kwargs = {}
        if len(list_args) > 0:
            if list_args[0] == 'filter':
                kwargs['filter'] = ' '.join(list_args[1:])
            else:
                kwargs['include'] = ' '.join(list_args[0:])

        requests = Request.get_online_requests(**kwargs)

        list_embed = EmbedBuilder().setTitle("**Villager Haven - Request List**") \
                                    .appendToDescription("**Next 20 Requests (to select, use `!select <number>`)**")
        request_lines = []
        for request in requests:
            request_user = CogHelpers.get_guild_member(request.member_id)
            if request_user is None:
                continue
            if len(request_user.display_name) > 10:
                member_name = request_user.display_name[0:10] + '.'
            else:
                member_name = request_user.display_name
            request_lines.append('{0} - **{1}** (**{2}**)'.format(member_name, request.member_id, request.villager_name))
        list_embed = list_embed.appendToDescription(request_lines)
            
        await ctx.send(embed=list_embed.build())

def setup(bot):
    bot.add_cog(QueueCog(bot))