import discord
import json
import os.path

class BotConfig:
    def __init__(self):
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