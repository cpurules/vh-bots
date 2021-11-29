import discord
import json
import os

class BotConfig:
    MAX_WINNERS_PER_GIVEAWAY_GROUP = 0
    MAX_WINNERS_PER_EVENT_GROUP = 0
    MAX_WINNERS_PER_POST = 20
    PITFALL_EMOJI = 0
    FAUNA_WAVE_EMOJI = 0
    EVENTS_TEAM_ROLE = 0
    GIVEAWAY_CATEGORY = 0
    EVENT_CATEGORY = 0
    GIVEAWAY_CHAT_CHANNEL = 0
    COURIER_ROLES = []
    CIT_ROLE = 0
    COURIER_MENTOR_ROLE = 0
    SEPARATE_CIT_CHANNEL = False
    SUPPLIER_ROLE = 0
    COMMAND_ENABLED_ROLES = []
    LOGGING_CHANNEL = 0

    def __init__(self, bot=None):
        self.bot = bot

        file = os.getenv("CONFIG_FILE")
        if file is None:
            raise ValueError("Missing CONFIG_FILE environment variable!")

        with open(file) as f:
            config_dict = json.load(f)
        
        self.MAX_WINNERS_PER_GIVEAWAY_GROUP = int(config_dict['MAX_WINNERS_PER_GIVEAWAY_GROUP'])
        if self.MAX_WINNERS_PER_GIVEAWAY_GROUP <= 0:
            raise ValueError("MAX_WINNERS_PER_GIVEAWAY_GROUP must be a positive integer")

        self.MAX_WINNERS_PER_EVENT_GROUP = int(config_dict['MAX_WINNERS_PER_EVENT_GROUP'])
        if self.MAX_WINNERS_PER_EVENT_GROUP <= 0:
            raise ValueError("MAX_WINNERS_PER_EVENT_GROUP must be a positive integer")

        self.MAX_WINNERS_PER_POST = int(config_dict['MAX_WINNERS_PER_POST'])
        if self.MAX_WINNERS_PER_POST <= 0 or self.MAX_WINNERS_PER_POST > 20:
            raise ValueError("MAX_WINNERS_PER_POST must be between 1 and 20, inclusive")
        
        self.PITFALL_EMOJI = int(config_dict['PITFALL_EMOJI'])
        if self.PITFALL_EMOJI <= 0:
            raise ValueError("You must specify PITFALL_EMOJI in " + file)
        
        self.FAUNA_WAVE_EMOJI = int(config_dict['FAUNA_WAVE_EMOJI'])
        if self.FAUNA_WAVE_EMOJI <= 0:
            raise ValueError("You must specify FAUNA_WAVE_EMOJI in " + file)
        
        self.EVENTS_TEAM_ROLE = int(config_dict['EVENTS_TEAM_ROLE'])
        if self.EVENTS_TEAM_ROLE <= 0:
            raise ValueError("You must specify EVENTS_TEAM_ROLE in " + file)

        self.GIVEAWAY_CATEGORY = int(config_dict['GIVEAWAY_CATEGORY'])
        if self.GIVEAWAY_CATEGORY <= 0:
            raise ValueError("You must specify the GIVEAWAY_CATEGORY category id in " + file)
        
        self.EVENT_CATEGORY = int(config_dict['EVENT_CATEGORY'])
        if self.EVENT_CATEGORY <= 0:
            raise ValueError("You must specify the EVENT_CATEGORY category id in " + file)
        
        self.GIVEAWAY_CHAT_CHANNEL = int(config_dict['GIVEAWAY_CHAT_CHANNEL'])
        if self.GIVEAWAY_CHAT_CHANNEL <= 0:
            raise ValueError("You must specify the GIVEAWAY_CHAT_CHANNEL channel id in " + file)

        self.COURIER_ROLES = config_dict['COURIER_ROLES']
        if len(self.COURIER_ROLES) == 0:
            raise ValueError("You must specify at least one role in COURIER_ROLES in " + file)
        
        self.CIT_ROLE = config_dict['CIT_ROLE']
        if self.CIT_ROLE <= 0:
            raise ValueError("You must specify the CIT_ROLE in " + file)

        self.COURIER_MENTOR_ROLE = config_dict['COURIER_MENTOR_ROLE']
        if self.COURIER_MENTOR_ROLE <= 0:
            raise ValueError("You must specify the COURIER_MENTOR_ROLE in " + file)

        self.SEPARATE_CIT_CHANNEL = bool(config_dict['SEPARATE_CIT_CHANNEL'])

        self.SUPPLIER_ROLE = int(config_dict['SUPPLIER_ROLE'])
        if self.SUPPLIER_ROLE <= 0:
            raise ValueError("You must specify the SUPPLIER_ROLE role id in " + file)

        self.COMMAND_ENABLED_ROLES = config_dict['COMMAND_ENABLED_ROLES']
        if len(self.COMMAND_ENABLED_ROLES) == 0:
            raise ValueError("You must specify at least one COMMAND_ENABLED_ROLES role in " + file)
        
        self.LOGGING_CHANNEL = int(config_dict['LOGGING_CHANNEL'])
        if self.LOGGING_CHANNEL <= 0:
            raise ValueError("You must specify the LOGGING_CHANNEL channel id in " + file)

    def GET_GUILD(self):
        if self.bot is None:
            raise ValueError("BotConfig bot is not defined!");
        
        return self.bot.guilds[0]
    
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
