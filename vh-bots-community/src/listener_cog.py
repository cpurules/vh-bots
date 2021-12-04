import asyncio
import discord
import random

from discord.guild import Guild

from award import Award
from award_channel import AwardChannel
from cog_helpers import CogHelpers
from discord.ext import commands
from member import GuildMember
from settings import *

# We want to avoid a database call to check chance configuration every message
LISTENER_SETTINGS = BotSettings.get_all_area_settings('activity')

class ListenerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        CogHelpers.set_bot(bot)

        ListenerCog.validate_listener_settings()
    
    #staticmethod
    def reload_listener_settings():
        LISTENER_SETTINGS = BotSettings.get_all_area_settings('activity')
        ListenerCog.validate_listener_settings()

    #staticmethod
    def validate_listener_settings():
        required_tokens = ['BASE_AWARD_CHANCE', 'AWARD_ENABLED_CHANNELS']
        for token in required_tokens:
            if not token in LISTENER_SETTINGS:
                raise KeyError("Missing required configuration token", token)
    
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot or isinstance(msg.channel, discord.DMChannel):
            return
        
        this_channel_id = msg.channel.id
        listening_channels = [AwardChannel.create_from_db_obj(x) for x in LISTENER_SETTINGS['AWARD_ENABLED_CHANNELS'].value]
        listening_channel = [x for x in listening_channels if x.id == this_channel_id]

        if not this_channel_id in [x.id for x in listening_channels] or len(listening_channel) == 0:
            return
        if GuildMember.get_member_by_id(msg.author.id) is None:
            return
        if msg.content.startswith("LF ") or msg.content.startswith("LF:"):
            return
        
        listening_channel = listening_channel[0]
        
        def calculate_award_chance():
            # multiply chance by 1.4^-n where n = number of awards the user has received in the past day
            repeat_multiplier = 1.4 ** (-1 * Award.count_user_awards(msg.author.id, past_hours=24))
            return (LISTENER_SETTINGS['BASE_AWARD_CHANCE'].value * listening_channel.frequency_multiplier) * repeat_multiplier
        
        def calculate_points():
            range_min, range_max = LISTENER_SETTINGS['BASE_AWARD_RANGE'].value
            return random.randrange(range_min * listening_channel.point_multiplier,  range_max * listening_channel.point_multiplier) + 1
        
        if random.random() < calculate_award_chance():
            # Queue a point reward for the person
            a = Award.queue_new_award(msg.id, msg.author.id, msg.jump_url, calculate_points())


def setup(bot):
    bot.add_cog(ListenerCog(bot))