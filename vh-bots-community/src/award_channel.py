from database import Database
from datetime import datetime, timedelta
from settings import BotSetting

class AwardChannel:
    def __init__(self, id: int, frequency_multiplier: float, point_multiplier: float):
        self.id = id
        self.frequency_multiplier = frequency_multiplier
        self.point_multiplier = point_multiplier
    
    @staticmethod
    def create_from_db_obj(db_obj):
        return AwardChannel(int(db_obj['id']), float(db_obj['frequency_multiplier']), float(db_obj['point_multiplier']))
    
    def get_as_db_dict(self):
        return {
            'id': str(self.id),
            'frequency_multiplier': float(self.frequency_multiplier),
            'point_multiplier': float(self.point_multiplier)
        }