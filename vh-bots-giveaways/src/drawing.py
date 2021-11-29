import asyncio
import discord
import time

from database import Database
from enum import Enum

class DrawingType(Enum):
    GIVEAWAY = 1
    EVENT = 2

    @staticmethod
    def from_str(label: str):
        if label.startswith('DrawingType.'):
            label = label.split('.')[1]
        if label.upper() in ['G', 'GIVEAWAY']:
            return DrawingType.GIVEAWAY
        elif label.upper() in ['E', 'EVENT']:
            return DrawingType.EVENT
        else:
            raise NotImplementedError('Unknown drawing type: ' + label)

class Drawing:
    # duration in seconds
    def __init__(self, start_time: int, winners, duration, claim_duration, prize, drawing_type, is_special, message_id: int=None, channel_id: int=None, ended_flag=False):
        self.message_id = message_id
        self.channel_id = channel_id
        self.start_time = start_time
        self.winners = winners
        self.duration = duration
        self.claim_duration = claim_duration
        self.prize = prize
        self.drawing_type = drawing_type
        self.is_special = is_special
        self.ended_flag = ended_flag

    @staticmethod
    def create_drawing_from_db_obj(db_object):
        return Drawing(db_object['start_time'], db_object['winners'], db_object['duration'], db_object['claim_duration'],
                        db_object['prize'], DrawingType.from_str(db_object['drawing_type']), db_object['is_special'], int(db_object['_key']), int(db_object['channel_id']), db_object['ended_flag']) 
    
    @staticmethod
    def get_all_drawings():
        db = Database()

        drawings = []
        for drawing in db.drawings.fetchAll():
            drawings.append(Drawing.create_drawing_from_db_obj(drawing))
        
        return drawings
    
    @staticmethod
    def get_all_active_drawings():
        db = Database()

        drawings = []
        aql_query = 'FOR d IN drawings FILTER d.ended_flag == false RETURN d'
        aql_result = db.db.AQLQuery(aql_query, rawResults=True)
        for result in aql_result:
            drawings.append(Drawing.create_drawing_from_db_obj(result))
        
        return drawings
    
    def create_in_db(self):
        if self.message_id is None or self.channel_id is None:
            raise ValueError("Cannot save to database without setting message and channel ids")
        
        db = Database()

        if str(self.message_id) in db.drawings:
            raise ValueError("This drawing already exists in the database")
        
        drawing = db.drawings.createDocument()
        drawing._key = str(self.message_id)
        drawing['channel_id'] = self.channel_id
        drawing['winners'] = self.winners
        drawing['start_time'] = self.start_time
        drawing['duration'] = self.duration
        drawing['claim_duration'] = self.claim_duration
        drawing['prize'] = self.prize
        drawing['drawing_type'] = self.drawing_type
        drawing['is_special'] = self.is_special
        drawing['ended_flag'] = self.ended_flag
        drawing.save()
    
    def end(self):
        drawing = self.get_drawing_db_object()
        drawing['ended_flag'] = True
        drawing.save()
        self.ended_flag = True
    
    def get_drawing_db_object(self):
        if self.message_id is None:
            return None

        db = Database()

        drawing = db.drawings.fetchDocument(str(self.message_id))
        return drawing
    
    def get_end_time(self):
        return self.start_time + self.duration

    def is_ended(self):
        return time.time() > self.get_end_time()
    
    def generate_embed(self):
        embed_title = 'Drawing for {0}'.format(self.prize)
        if(self.is_ended()):
            embed_desc = "This drawing has ended.  Congratulations to the winners!"
            embed_color = 0x871616
            embed_remaining = "Ended"
        else:
            embed_desc = "React with \N{PARTY POPPER} to enter!"
            embed_color = 0x248617
            embed_remaining = self.format_time_remaining()
        
        embed = discord.Embed(title=embed_title, description=embed_desc, color=embed_color)
        embed.add_field(name="Winners", value=self.winners)
        embed.add_field(name="Time Remaining", value=embed_remaining)
        return embed
    
    def set_ids(self, message):
        self.message_id = message.id
        self.channel_id = message.channel.id
    
    #TODO get message from message_id
    async def update_embed(self):
        await self.msg.edit(embed=self.generate_embed())

    def time_remaining(self):
        return max(0, self.start_time + self.duration - int(time.time()))

    def time_to_next_update(self):
        time_remaining = self.time_remaining()
        # > 1 day remaining, update every hour
        if(time_remaining > (60 * 60 * 24)):
            return (60 * 60)
        # 1 hour < x <= 1 day remaining, update every 30 minutes
        elif(time_remaining > (60 * 60)):
            return (60 * 30)
        # 20 minutes < x <= 1 hour remaining, update every 10 minutes
        elif(time_remaining > (60 * 20)):
            return (60 * 10)
        # 5 minutes < x <= 20 minutes remaining, update every minute
        elif(time_remaining > (60 * 5)):
            return (60)
        # 1 minute < x <= 5 minutes remaining, update every 30 seconds
        elif(time_remaining > 60):
            return (30)
        # 10 secs < x <= 1 minute remaining, update every 5 seconds
        elif(time_remaining > 10):
            return (5)
        # <= 10 secs remaining, update every second
        else:
            return (1)
    
    def format_time_remaining(self):
        return Drawing.format_duration(self.time_remaining())
    
    @staticmethod
    def format_duration(duration):
        duration_remaining = duration

        days = 0
        hours = 0
        mins = 0
        secs = 0

        if duration_remaining >= (60 * 60 * 24):
            days = int(duration_remaining / (60 * 60 * 24))
            duration_remaining = duration_remaining - (days * 60 * 60 * 24)
        if duration_remaining >= (60 * 60):
            hours = int(duration_remaining / (60 * 60))
            duration_remaining = duration_remaining - (hours * 60 * 60)
        if duration_remaining >= 60:
            mins = int(duration_remaining / 60)
            duration_remaining = duration_remaining - (mins * 60)
        
        secs = duration_remaining
        formatted_durations = []

        if(days > 0):
            span = "day"
            if(days != 1):
                span += "s"
            formatted_durations.append("{0} {1}".format(days, span))
        if(hours > 0 or (days > 0 and (mins > 0 or secs > 0))):
            # if there are hours, we want to include them
            # if there are not hours, but we have days and either mins or secs, include
            span = "hour"
            if(hours != 1):
                span += "s"
            formatted_durations.append("{0} {1}".format(hours, span))
        if(mins > 0 or ((days > 0 or hours > 0) and secs > 0)):
            # if there are minutes, we want to include them
            # if there are not minutes, but we have either days or hours, and we have secs, include
            span = "minute"
            if(mins != 1):
                span += "s"
            formatted_durations.append("{0} {1}".format(mins, span))
        if(secs > 0):
            # if there are seconds, include them
            span = "second"
            if(secs != 1):
                span += "s"
            formatted_durations.append("{0} {1}".format(secs, span))
        
        return ', '.join(formatted_durations)