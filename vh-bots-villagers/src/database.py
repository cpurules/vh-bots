import json
import os.path

from pyArango.connection import *

class Database:
    def __init__(self, file='dbconfig.json'):
        if not os.path.exists(file):
            raise FileNotFoundError('Could not find configuration file: ' + file)
        
        with open(file) as f:
            try:
                config_dict = json.load(f)
            except Exception as e:
                raise Exception('Error while parsing ' + file + ': ' + e)
        
        required_fields = ['DB_SERVER', 'DB_PORT', 'DB_USER', 'DB_DATABASE']
        for field in required_fields:
            if not field in config_dict:
                raise KeyError('Missing field from ' + file + ': ' + field)
            if not config_dict[field]:
                raise ValueError('No value specified for field ' + field)

        try:
            int(config_dict['DB_PORT'])
        except ValueError:
            raise ValueError('Invalid value specified for DB_PORT: ' + config_dict['DB_PORT'])
        
        arangoURL = 'http://{0}:{1}'.format(config_dict['DB_SERVER'], config_dict['DB_PORT'])
        try:
            conn = Connection(arangoURL=arangoURL, username=config_dict['DB_USER'], password=os.getenv('ARANGODB_PASSWORD', ''))
        except Exception:
            raise RuntimeError('Unable to connect to ArangoDB at {0}.  Please verify the server and logon settings'.format(arangoURL))
        
        db_exists = conn.hasDatabase(config_dict['DB_DATABASE'])
        
        if not db_exists:
            raise KeyError('The database specified does not exist: {0}'.format(config_dict['DB_DATABASE']))
        
        self.db = conn[config_dict['DB_DATABASE']]
        
        try:
            self.requests = self.db['requests']
            self.reservations = self.db['reservations']
            self.blocks = self.db['blocks']
        except KeyError:
            raise KeyError('Missing required database collection')