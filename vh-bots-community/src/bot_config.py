import discord
import json
import os.path

from settings import *

class BotConfig:
    def __init__(self, bot=None):
        self.bot = bot

        config_file = os.getenv('CONFIG_FILE')
        if config_file is None or config_file == '':
            raise ValueError('CONFIG_FILE environment variable is not set')
        
        if not os.path.exists(config_file):
            raise FileNotFoundError('Could not find configuration file: ' + config_file)
        
        with open(config_file) as f:
            try:
                config_dict = json.load(f)
            except Exception as e:
                raise Exception('Error while parsing {0}: {1}'.format(config_file, str(e)))

        try:
            try:
                self.GUILD_ID = int(config_dict['GUILD_ID'])
                if self.GUILD_ID == 0:
                    raise ValueError('No value specified')
            except ValueError as e:
                raise ValueError('Error while parsing GUILD_ID: ' + str(e))
            
            self.TOKEN = os.getenv('BOT_TOKEN')
            if self.TOKEN is None or self.TOKEN == '':
                raise ValueError('BOT_TOKEN OS variable is not set')

        except KeyError as e:
            raise KeyError('{0} missing from {1}'.format(str(e), config_file))

    @staticmethod
    def to_list(obj):
        if isinstance(obj, list):
            return obj
        else:
            return [obj]
    
    #TODO these are getting moved to cog_helpers
    def GET_GUILD(self):
        if self.bot is None:
            raise ValueError('BotConfig bot is not defined!')
        
        guild = discord.utils.get(self.bot.guilds, id=self.GUILD_ID)
        if guild is None:
            raise RuntimeError('Bot is not a member of guild ' + str(self.GUILD_ID))
        
        return guild
        
    def get_guild_member(self, member_id):
        guild = self.GET_GUILD()
        return guild.get_member(member_id)
    
    def get_guild_role_by_name(self, role_name):
        guild = self.GET_GUILD()
        return discord.utils.get(guild.roles, name=role_name)
    
    def get_guild_role_by_id(self, role_id):
        guild = self.GET_GUILD()
        return discord.utils.get(guild.roles, id=role_id)
    
    def get_guild_channel_by_id(self, channel_id):
        guild = self.GET_GUILD()
        return discord.utils.get(guild.channels, id=channel_id)
    
    def get_user_full_name(self, discord_user):
        if discord_user is None:
            return None
        else:
            return "{0}#{1}".format(discord_user.name, discord_user.discriminator)
    
    def set_bot(self, bot):
        self.bot = bot