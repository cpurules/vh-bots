import asyncio
import discord

from award import Award
from bot_config import BotConfig
from cog_helpers import CogHelpers
from datetime import datetime, timedelta
from discord.ext import commands
from discord.ext import tasks
from embed_builder import EmbedBuilder
from member import GuildMember
from settings import *

# We want to avoid a database call to check chance configuration every message
BACKGROUND_SETTINGS = BotSettings.get_all_area_settings('background')
CONFIG = BotConfig()

class BackgroundCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CONFIG.set_bot(bot)
        CogHelpers.set_bot(bot)

        BackgroundCog.validate_background_settings()
        self.process_award_queue.start()

    #staticmethod
    def reload_background_settings():
        BACKGROUND_SETTINGS = BotSettings.get_all_area_settings('background')
        BackgroundCog.validate_backgorund_settings()

    #staticmethod
    def validate_background_settings():
        required_tokens = ['AWARD_PROCESS_DELAY', 'AWARD_PROCESS_INTERVAL', 'PROCESS_AWARDS']
        for token in required_tokens:
            if not token in BACKGROUND_SETTINGS:
                raise KeyError("Missing required configuration token", token)

    @tasks.loop(seconds=BACKGROUND_SETTINGS['AWARD_PROCESS_INTERVAL'].value*60)
    async def process_award_queue(self):
        should_process = bool(BACKGROUND_SETTINGS['PROCESS_AWARDS'].value)
        if not should_process:
            return

        queued_awards = Award.get_queued_awards()
        time_delta = timedelta(minutes=BACKGROUND_SETTINGS['AWARD_PROCESS_DELAY'].value)
        for queued_award in queued_awards:
            # Check for message deletion
            # Link format: https://discord.com/channels/guild/channel/message
            channel_id = int(queued_award.link.split('/')[-2])
            channel = CONFIG.get_guild_channel_by_id(channel_id)
            
            deleted = False
            if channel is None:
                deleted = True
            else:
                try:
                    msg = await channel.fetch_message(queued_award.message)
                except discord.errors.NotFound:
                    deleted = True

            if deleted:
                queued_award.mark_deleted()           
            elif datetime.now() > (queued_award.queued_at + time_delta):
                member = GuildMember.get_member_by_id(queued_award.author)
                member.process_award(queued_award)
                queued_award.award()

    @process_award_queue.before_loop
    async def before_process_award_queue(self):
        await self.bot.wait_until_ready()

    @commands.command(name='pendingawards')
    @commands.check(CogHelpers.check_is_admin)
    @commands.check(CogHelpers.check_is_channel_or_dm)
    async def list_queued_awards(self, ctx):
        queued_awards = Award.get_queued_awards()
        
        awards_embed = EmbedBuilder().setTitle("Pending Award Queue") \
                                        .setColour(BotSettings.get_setting('admin', 'EMBED_COLOUR').value)

        embed_lines = []
        line_num = 1
        for award in queued_awards:
            embed_lines.append("**{0}**. {1}".format(line_num, str(award)))
            line_num += 1
            if line_num > 10:
                break

        if len(embed_lines) == 0:
            embed_lines = ["No pending awards!"]
        
        awards_embed.setDescriptionFromLines(embed_lines)

        await ctx.send(embed=awards_embed.build())


def setup(bot):
    bot.add_cog(BackgroundCog(bot))