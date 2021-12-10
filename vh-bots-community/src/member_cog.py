import asyncio
import discord

from cog_helpers import CogHelpers
from discord.ext import commands
from embed_builder import EmbedBuilder
from award import Award
from member import GuildMember
from settings import *

class GuildMemberCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)
    
    @commands.command(name='balance')
    @commands.check(CogHelpers.check_is_guild_member)
    @commands.dm_only()
    async def check_balance(self, ctx):
        has_profile = await CogHelpers.require_bot_membership(ctx)
        if not has_profile:
            return

        profile = GuildMember.get_member_by_id(ctx.author.id)

        balance_embed = EmbedBuilder().setTitle("Point Balance") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value) \
                                        .appendToDescription("Hello {0}!".format(ctx.author.mention)) \
                                        .appendToDescription("You currently have **{0}** points".format(profile.balance))
        
        await ctx.send(embed=balance_embed.build())

    @commands.command(name='join')
    @commands.check(CogHelpers.check_is_guild_member)
    @commands.dm_only()
    async def join_community_bot(self, ctx):
        user_id = ctx.author.id
        profile = GuildMember.get_member_by_id(user_id)
        
        created = False
        if profile is None:
            profile = GuildMember.create_member(user_id)
            created = True
        
        reply_embed = EmbedBuilder().setTitle('VH Community Bot') \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
        if created:
            reply_embed = reply_embed.appendToDescription("Thanks for joining in!") \
                                        .appendToDescription("We've credited you {0} points as a welcome and thank you!".format(profile.balance))
        else:
            reply_embed = reply_embed.appendToDescription("You've already joined!") \
                                        .appendToDescription("You can check your current point balance with `c.balance`")
        
        await ctx.send(embed=reply_embed.build())
    
    @commands.command(name='award')
    @commands.check(CogHelpers.check_is_admin)
    @commands.check(CogHelpers.check_is_channel_or_dm)
    async def award_points(self, ctx, member_id: int=None, points_delta: int=None):
        if member_id is None or points_delta is None:
            await ctx.invoke(self.bot.get_command('c.help'), flag='c.award')
            return
        
        award_embed = EmbedBuilder().setTitle('Award Points to Guild Member') \
                                    .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
        
        embed_lines = []
        member = GuildMember.get_member_by_id(member_id)
        if member is None:
            embed_lines.append("There is currently no community member profile for ID `{0}` (<@{0}>)".format(member_id))
        else:
            try:
                points_delta = int(points_delta)
            except ValueError:
                embed_lines.append("Cannot award invalid number of points `{0}`".format(points_delta))
            else:
                member.adjust_balance(points_delta)
                embed_lines.append("Updated balance for user ID `{0}` ({1}) by {2} points (now: {3})".format(member_id, member.get_mention(), points_delta, member.balance))
        
        award_embed = award_embed.setDescriptionFromLines(embed_lines) \
                                .build()
        
        await ctx.send(embed=award_embed)
    
    @commands.command(name='awardhistory')
    @commands.check(CogHelpers.check_is_admin)
    @commands.check(CogHelpers.check_is_channel_or_dm)
    async def get_award_history(self, ctx, member_id: int=None):
        if member_id is None:
            await ctx.invoke(self.bot.get_command('c.help'), flag='c.awardhistory')
            return
        
        history_embed = EmbedBuilder().setTitle('Award History') \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
        embed_lines = []

        member = GuildMember.get_member_by_id(member_id)
        if member is None:
            embed_lines.append("I can't find member with ID `{0}` (<@{0}>)".format(member_id))
        else:
            award_history = Award.get_user_award_history(member_id, max_count=10)
            embed_lines.append("**__Last 10 awards for user <@{0}>__**".format(member_id))
            for award in award_history:
                embed_lines.append(str(award))
        
        history_embed = history_embed.appendToDescription(embed_lines)
        await ctx.send(embed=history_embed.build())

    @commands.command(name='lookup')
    @commands.check(CogHelpers.check_is_admin)
    @commands.check(CogHelpers.check_is_channel_or_dm)
    async def lookup_member(self, ctx, member_id: int=None):
        if member_id is None:
            await ctx.invoke(self.bot.get_command('c.help'), flag='c.lookup')
            return
        
        info_embed = EmbedBuilder().setTitle('Guild Member Profile') \
                                    .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
    
        embed_lines = []
        member = GuildMember.get_member_by_id(member_id)
        if member is None:
            embed_lines.append("There is currently no community member data for ID `{0}` (<@{0}>)".format(member_id))
        else:
            embed_lines.append("Member data found for ID `{0}` ({1})\n".format(member_id, member.get_mention()))
            embed_lines.append("**Balance** - {0}".format(member.balance))
        
        info_embed = info_embed.setDescriptionFromLines(embed_lines) \
                                .build()
        
        await ctx.send(embed=info_embed)
    
    @commands.command(name='setbalance')
    @commands.check(CogHelpers.check_is_admin)
    @commands.check(CogHelpers.check_is_channel_or_dm)
    async def set_member_balance(self, ctx, member_id: int=None, new_balance: int=None):
        if member_id is None or new_balance is None:
            await ctx.invoke(self.bot.get_command('c.help'), flag='c.setbalance')
            return
        
        update_embed = EmbedBuilder().setTitle('Update Guild Member Balance') \
                                    .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)
        
        embed_lines = []
        member = GuildMember.get_member_by_id(member_id)
        if member is None:
            embed_lines.append("There is currently no community member profile for ID `{0}` (<@{0}>)".format(member_id))
        else:
            try:
                new_balance = int(new_balance)
                if new_balance < 0:
                    raise ValueError("Point balances can only be positive numbers", new_balance)
            except ValueError:
                embed_lines.append("Cannot set balance to invalid value `{0}`".format(new_balance))
            else:
                member.set_balance(new_balance)
                embed_lines.append("Updated balance for user ID `{0}` ({1}) to {2}".format(member_id, member.get_mention(), new_balance))
        
        update_embed = update_embed.setDescriptionFromLines(embed_lines) \
                                .build()
        
        await ctx.send(embed=update_embed)


def setup(bot):
    bot.add_cog(GuildMemberCog(bot))