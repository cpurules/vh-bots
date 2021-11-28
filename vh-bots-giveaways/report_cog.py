import asyncio
import discord

from config import BotConfig
from discord.ext import commands

CONFIG = BotConfig()

class ReportCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='citreport')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def get_cit_report(self, ctx, giveaway_id: str=''):
        if giveaway_id == '':
            await ctx.send('Usage: !citreport <id>')
            return

        await ctx.invoke(self.bot.get_command('report'), giveaway_id=giveaway_id)
    
    @commands.command(name='report')
    @commands.has_any_role(*CONFIG.COMMAND_ENABLED_ROLES)
    async def get_courier_report(self, ctx, giveaway_id: str=''):
        if giveaway_id == '':
            await ctx.send('Usage: !report <id>')
            return
        
        cit_only = True if ctx.command.name == 'citreport' else False
        
        max_message_history = CONFIG.MAX_WINNERS_PER_GIVEAWAY_GROUP * 2

        # check for channel existence
        channels = []
        for channel in ctx.guild.text_channels:
            if channel.name.startswith('winners-{0}'.format(giveaway_id)):
                channels.append(channel)
        
        if len(channels) == 0 and giveaway_id.isnumeric():
            # maybe this is an individual channel, so let's look for that instead
            channel = discord.utils.get(ctx.guild.text_channels, id=int(giveaway_id))
            if not channel is None:
                channels.append(channel)
                giveaway_id = '#{0}'.format(channel.name)
                max_message_history = 500
        
        if len(channels) == 0:
            # neither returned anything
            await ctx.send('Could not find any channels for ID: {0}'.format(giveaway_id))
            return
        
        couriers = {}
        for channel in channels:
            async for message in channel.history(limit=max_message_history):
                reacts = message.reactions
                for react in reacts:
                    if react.emoji == '\N{CROSS MARK}':
                        reacters = await react.users().flatten()
                        for courier in reacters:
                            if not type(courier) is discord.Member:
                                continue
                            elif cit_only and discord.utils.get(courier.roles, id=CONFIG.CIT_ROLE) is None:
                                continue

                            courier_id = courier.id
                            if not courier_id in couriers:
                                couriers[courier_id] = 1
                            else:
                                couriers[courier_id] += 1
                        break
        
        total_delivered = sum(couriers.values())
        
        # Create embed for post
        if cit_only:
            title_desc = 'Courier-In-Training'
        else:
            title_desc = 'All Courier'

        embed_title = '{0} Deliveries for Giveaway {1}'.format(title_desc, giveaway_id.upper())
        embed_color = 0xEBAE34
        embed_lines = ['**Total Deliveries Made:** {0}'.format(total_delivered), '']

        couriers_sorted = dict(reversed(sorted(couriers.items(), key=lambda item: item[1])))

        for courier in couriers_sorted:
            courier_as_member = CONFIG.get_guild_member(courier)
            if courier_as_member is None:
                continue
            courier_full_name = courier_as_member.name + '#' + courier_as_member.discriminator
            courier_deliveries = couriers_sorted[courier]
            embed_lines.append('**{0}** - {1}'.format(courier_full_name, courier_deliveries))
        
        embed_desc = '\r\n'.join(embed_lines)
        embed = discord.Embed(title=embed_title, description=embed_desc, color=embed_color)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(ReportCog(bot))
    CONFIG.bot = bot