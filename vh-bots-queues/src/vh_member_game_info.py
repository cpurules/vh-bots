from database import Database
from datetime import datetime

# A note on Discord ID typing:
# Discord IDs are 18-digit integer values
# ArangoDB has the following limitations:
# - Document keys are not allowed to be numbers, they must be strings
# --- Since our document key is the queue owner Discord ID, we must convert from int->string for key purposes
# - Numeric data types are double-precision floats
# --- After 2^53, we lose integer-level precision.  This makes double-precision floats problematic for Discord IDs
# --- Thus we convert from int->string for DB storage purposes
# It should be noted that the type hints and methods work based off of integer IDs, since that is what we get from
# discord.py; however they are stored in the database as strings

class VHMemberGameInfo:
    def __init__(self, discord_id: int, island_name: str=None, player_name: str=None, timestamp: str=None, change_count: int=None):
        self.discord_id = discord_id
        self.island_name = island_name
        self.player_name = player_name
        self.timestamp = timestamp
        self.change_count = change_count
    
    @staticmethod
    def create_mgi_from_db_obj(db_object):
        return VHMemberGameInfo(int(db_object['_key']), db_object['island_name'], db_object['player_name'], db_object['timestamp'],
                                int(db_object['change_count']))
    
    @staticmethod
    def get_mgi_by_user(discord_id: int):
        db = Database()

        if not str(discord_id) in db.member_game_info:
            return None

        member_game_info = db.member_game_info[str(discord_id)]
        
        return VHMemberGameInfo.create_mgi_from_db_obj(member_game_info)

    @staticmethod
    def insert_member_game_info(discord_id: int, island_name: str, player_name: str):
        db = Database()

        if str(discord_id) in db.member_game_info:
            raise ValueError('Game info already exists for {0}'.format(discord_id))

        member_game_info = db.member_game_info.createDocument()
        member_game_info['island_name'] = island_name
        member_game_info['player_name'] = player_name
        member_game_info['timestamp'] = str(datetime.now())
        member_game_info['change_count'] = 0
        member_game_info._key = str(discord_id)
        member_game_info.save()

        return VHMemberGameInfo(discord_id, island_name, player_name, member_game_info['timestamp'], member_game_info['change_count'])
    
    def get_mgi_db_object(self):
        db = Database()

        member_game_info = db.member_game_info.fetchDocument(str(self.discord_id))
        return member_game_info
    
    def set_island_name(self, island_name: str):
        member_game_info = self.get_mgi_db_object()
        member_game_info['island_name'] = island_name
        member_game_info['timestamp'] = str(datetime.now())
        member_game_info['change_count'] += 1
        member_game_info.save()
        self.update_fields(member_game_info)
    
    def set_player_name(self, player_name: str):
        member_game_info = self.get_mgi_db_object()
        member_game_info['player_name'] = player_name
        member_game_info['timestamp'] = str(datetime.now())
        member_game_info['change_count'] += 1
        member_game_info.save()
        self.update_fields(member_game_info)
    
    def update_fields(self, member_game_info):
        self.island_name = member_game_info['island_name']
        self.player_name = member_game_info['player_name']
        self.timestamp = member_game_info['timestamp']
        self.change_count = member_game_info['change_count']