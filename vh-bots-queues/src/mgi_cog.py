import asyncio
import bot_config
import discord
import re

from discord.ext import commands
from vh_member_game_info import VHMemberGameInfo

CONFIG = bot_config.BotConfig()

class MemberGameInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def can_create_queue(ctx):
        user_id = ctx.message.author.id

        member = CONFIG.get_guild_member(user_id)
        if member is None:
            return False
        
        if member.id in CONFIG.CREATE_QUEUE_USERS:
            return True

        for member_role in member.roles:
            if member_role.id in CONFIG.CREATE_QUEUE_ROLES:
                return True
        
        return False

    def is_guild_member(ctx):
        user_id = ctx.message.author.id

        member = CONFIG.get_guild_member(user_id)
        return not member is None
    
    async def edit_game_info(self, ctx):
        msg = await ctx.send(content='If you would like to edit your **__island name__**, please click the \N{DESERT ISLAND} react!\n' +
                                'If you would like to edit your **__player name__**, please click the \N{FACE WITHOUT MOUTH} react!')

        react_emojis = ['\N{DESERT ISLAND}', '\N{FACE WITHOUT MOUTH}']
        for react in react_emojis:
            await msg.add_reaction(react)

        def validate_react(react, user):
            return react.emoji in react_emojis and user.id == ctx.author.id and react.message.id == msg.id
        
        try:
            react = await self.bot.wait_for('reaction_add', check=validate_react, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(content='You took too long to reply!  Use `q.gameinfo` to start over.')
            return
        else:
            react = react[0]
            if react.emoji == '\N{DESERT ISLAND}':
                await self.edit_island_name(ctx)
            elif react.emoji == '\N{FACE WITHOUT MOUTH}':
                await self.edit_player_name(ctx)
    
    async def edit_island_name(self, ctx):
        msg = await ctx.send(content='Please enter the name of your **__island__**')

        def validate_response(message):
            return message.channel == msg.channel and message.author.id == ctx.author.id
        
        valid_island_name = False
        while not valid_island_name:
            try:
                message = await self.bot.wait_for('message', check=validate_response, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(content='You took too long to reply!  Use `q.gameinfo` to start over.')
                return
            else:
                island_name = message.content.strip()
                if len(island_name) == 0 or len(island_name) > 10:
                    await ctx.send(content='Island names can only be up to 10 characters.\nPlease enter the name of your **__island__**')
                else:
                    valid_island_name = True

        member_game_info = VHMemberGameInfo.get_mgi_by_user(message.author.id)
        member_game_info.set_island_name(island_name)
        await ctx.send(content='Updated island name to {0}'.format(island_name))
    
    async def edit_player_name(self, ctx):
        msg = await ctx.send(content='Please enter the name of your **__resident/character__**')

        def validate_response(message):
            return message.channel == msg.channel and message.author.id == ctx.author.id
        
        valid_player_name = False
        while not valid_player_name:
            try:
                message = await self.bot.wait_for('message', check=validate_response, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(content='You took too long to reply!  Use `q.gameinfo` to start over.')
                return
            else:
                player_name = message.content.strip()
                if len(player_name) == 0 or len(player_name) > 10:
                    await ctx.send(content='Player names can only be up to 10 characters.\nPlease enter the name of your **__resident/character__**')
                else:
                    valid_player_name = True
        
        member_game_info = VHMemberGameInfo.get_mgi_by_user(message.author.id)
        member_game_info.set_player_name(player_name)
        await ctx.send(content='Updated player name to {0}'.format(player_name))
    
    async def new_game_info(self, ctx):
        msg = await ctx.send(content='Please enter the name of your **__island__**')

        def validate_response(message):
            return message.channel == msg.channel and message.author.id == ctx.author.id
        
        valid_island_name = False
        while not valid_island_name:
            try:
                message = await self.bot.wait_for('message', check=validate_response, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send(content='You took too long to reply!  Use `q.gameinfo` to start over.')
                return
            else:
                island_name = message.content.strip()
                if len(island_name) == 0 or len(island_name) > 10:
                    await ctx.send(content='Island names can only be up to 10 characters.\nPlease enter the name of your **__island__**')
                else:
                    valid_island_name = True

        msg = await ctx.send(content='Please enter the name of your **__resident/character__**')
        valid_player_name = False
        while not valid_player_name:
                try:
                    message = await self.bot.wait_for('message', check=validate_response, timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send(content='You took too long to reply!  Use `q.gameinfo` to start over.')
                    return
                else:
                    player_name = message.content.strip()
                    if len(player_name) == 0 or len(player_name) > 10:
                        await ctx.send(content='Player names can only be up to 10 characters.\nPlease enter the name of your **__resident/character__**')
                    else:
                        valid_player_name = True

        member_game_info = VHMemberGameInfo.insert_member_game_info(message.author.id, island_name, player_name)
        await ctx.send(content='Successfully saved your ACNH game info!')

    @commands.command(name='gameinfo')
    @commands.check(is_guild_member)
    @commands.dm_only()
    async def get_game_info(self, ctx, *, user_id: int=None):
        if user_id is None or not MemberGameInfoCog.can_create_queue(ctx):
            member_game_info = VHMemberGameInfo.get_mgi_by_user(ctx.author.id)
            user_name = CONFIG.get_user_full_name(ctx.author)
        else:
            member_game_info = VHMemberGameInfo.get_mgi_by_user(user_id)
            user_name = CONFIG.get_user_full_name(CONFIG.get_guild_member(user_id))
        
        embed_title = 'ACNH Game Data for {0}'.format(user_name)
        embed_color = 0xFFFFFF
        embed = discord.Embed(title=embed_title, color=embed_color)
        if member_game_info is None:
            embed.description = "You don't have any ACNH info saved!"
        else:
            embed.add_field(name='Island Name', value=member_game_info.island_name)
            embed.add_field(name='Player Name', value=member_game_info.player_name)
        
        await ctx.send(embed=embed)

        if not user_id is None and MemberGameInfoCog.can_create_queue(ctx):
            return
            
        base_msg = "To create or edit your ACNH game info, {0}"

        msg = await ctx.send(content=base_msg.format("click the \N{PENCIL} react below in the next 30 seconds!"))
        await msg.add_reaction('\N{PENCIL}')

        def validate_react(react, user):
            return react.emoji == '\N{PENCIL}' and user.id == ctx.author.id and react.message.id == msg.id
            
        try:
            react = await self.bot.wait_for('reaction_add', check=validate_react, timeout=30)
        except asyncio.TimeoutError:
            await msg.remove_reaction('\N{PENCIL}', self.bot.user)
            await msg.edit(content=base_msg.format("use `q.gameinfo` and click the \N{PENCIL} react!"))
        else:
            if member_game_info is None:
                await self.new_game_info(ctx)
            else:
                await self.edit_game_info(ctx)
    
    @commands.command(name='getinfo')
    @commands.check(can_create_queue)
    @commands.dm_only()
    async def check_game_info(self, ctx, discord_id: int):
        member = CONFIG.get_guild_member(discord_id)
        if member is None:
            await ctx.send(content='Could not find guild member with ID: `{0}`'.format(discord_id))
            return
        
        member_game_info = VHMemberGameInfo.get_mgi_by_user(discord_id)
        
        user_name = CONFIG.get_user_full_name(member)
        embed_title = 'ACNH Game Data for {0}'.format(user_name)
        embed_color = 0xFFFFFF
        embed = discord.Embed(title=embed_title, color=embed_color)
        if member_game_info is None:
            embed.description = "You don't have any ACNH info saved!"
        else:
            embed.add_field(name='Island Name', value=member_game_info.island_name)
            embed.add_field(name='Player Name', value=member_game_info.player_name)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='whois')
    async def lookup_members(self, ctx, type: str, search: str):
        return

def setup(bot):
    bot.add_cog(MemberGameInfoCog(bot))
    CONFIG.bot = bot