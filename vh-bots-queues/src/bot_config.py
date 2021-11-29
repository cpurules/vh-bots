import discord
import json
import os

class BotConfig:
    def __init__(self, bot=None):
        self.bot = bot

        self.TOKEN = os.getenv('BOT_TOKEN')
        if self.TOKEN is None or self.TOKEN == '':
            raise ValueError('BOT_TOKEN environment variable is not set')

        file = os.getenv('CONFIG_FILE')
        if file is None or file == '':
            raise ValueError('CONFIG_FILE environment variable is not set')
        elif not os.path.exists(file):
            raise FileNotFoundError('Could not find configuration file: ' + file)
        
        with open(file) as f:
            try:
                config_dict = json.load(f)
            except Exception as e:
                raise Exception('Error while parsing ' + file + ': ' + str(e))
        
        try:
            try:
                self.CREATE_QUEUE_ROLES = [int(x) for x in config_dict['CREATE_QUEUE_ROLES']]
            except ValueError as e:
                raise ValueError('Error while parsing CREATE_QUEUE_ROLES: ' + str(e))

            try:
                self.CREATE_QUEUE_USERS = [int(x) for x in config_dict['CREATE_QUEUE_USERS']]
            except ValueError as e:
                raise ValueError('Error while parsing CREATE_QUEUE_USERS: ' + str(e))
            
            try:
                self.EVENTS_TEAM_ROLE = int(config_dict['EVENTS_TEAM_ROLE'])
                if self.EVENTS_TEAM_ROLE == 0:
                    raise ValueError('No value specified')
            except ValueError as e:
                raise ValueError('Error while parsing EVENTS_TEAM_ROLE: ' + str(e))
            
            try:
                self.GUILD_ID = int(config_dict['GUILD_ID'])
                if self.GUILD_ID == 0:
                    raise ValueError('No value specified')
            except ValueError as e:
                raise ValueError('Error while parsing GUILD_ID: ' + str(e))

            try:
                self.OWNER_ROLES = [int(x) for x in config_dict['OWNER_ROLES']]
            except ValueError as e:
                raise ValueError('Error while parsing OWNER_ROLES: ' + str(e))

            try:
                self.QUEUE_CATEGORY = int(config_dict['QUEUE_CATEGORY'])
                if self.QUEUE_CATEGORY == 0:
                    raise ValueError('No value specified')
            except ValueError as e:
                raise ValueError('Error while parsing QUEUE_CATEGORY: ' + str(e))

            try:
                self.REMOVE_ROLE_ON_LEAVE = bool(config_dict['REMOVE_ROLE_ON_LEAVE'])
            except ValueError as e:
                raise ValueError('Error while parsing REMOVE_ROLE_ON_LEAVE: ' + str(e))

        except KeyError as e:
            raise KeyError(str(e) + ' missing from ' + file)
    
    def GET_GUILD(self):
        if self.bot is None:
            raise ValueError('BotConfig bot is not defined')

        bot_guild = discord.utils.get(self.bot.guilds, id=self.GUILD_ID)
        if bot_guild is None:
            raise RuntimeError('Bot is not a member of guild ' + self.GUILD_ID)
        
        return bot_guild
    
    def get_guild_text_channel(self, id):
        bot_guild = self.GET_GUILD()
        return discord.utils.get(bot_guild.text_channels, id=id)

    def get_guild_member(self, id):
        bot_guild = self.GET_GUILD()
        return bot_guild.get_member(id)
    
    def get_guild_role_by_name(self, name):
        bot_guild = self.GET_GUILD()
        return discord.utils.get(bot_guild.roles, name=name)
    
    def get_guild_role_by_id(self, id):
        bot_guild = self.GET_GUILD()
        return discord.utils.get(bot_guild.roles, id=id)
    
    def get_user_full_name(self, discord_user):
        if discord_user is None:
            return None
        else:
            return "{0}#{1}".format(discord_user.name, discord_user.discriminator)
