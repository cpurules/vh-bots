import random

from database import Database

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

class VHQueue:
    def __init__(self, owner_id: int, max_size: int, max_at_once: int, dodo_code: str, island_name: str, is_locked: bool, join_code: str, channel_id: int=None, roster_message_id: int=None):
        self.owner_id = owner_id
        self.max_size = max_size
        self.max_at_once = max_at_once
        self.dodo_code = dodo_code
        self.island_name = island_name
        self.is_locked = is_locked
        self.join_code = join_code
        self.channel_id = channel_id
        self.roster_message_id = roster_message_id
    
    @staticmethod
    def create_join_code():
        db = Database()

        letters = [chr(x) for x in range(ord('a'), ord('f')+1)]
        join_code = ''
        while join_code == '':
            new_join_code = ''.join(random.choices(letters, k=4))
            existing_queue = VHQueue.get_queue_by_join_code(new_join_code)
            if existing_queue is None:
                join_code = new_join_code
        
        return join_code
    
    @staticmethod
    def create_new_queue(owner_id: int, max_size: int, max_at_once: int, dodo_code: str, island_name: str, is_locked: bool):
        db = Database()

        if str(owner_id) in db.queues:
            raise ValueError('Queue already exists for {0}'.format(owner_id))
        
        join_code = VHQueue.create_join_code()

        queue = db.queues.createDocument()
        queue['max_size'] = max_size
        queue['max_at_once'] = max_at_once
        queue['dodo_code'] = dodo_code
        queue['island_name'] = island_name
        queue['is_locked'] = is_locked
        queue['join_code'] = join_code
        queue._key = str(owner_id)
        queue.save()

        return VHQueue(owner_id, max_size, max_at_once, dodo_code, island_name, is_locked, join_code)
    
    @staticmethod
    def create_queue_from_db_obj(db_object):
        return VHQueue(int(db_object['_key']), db_object['max_size'], db_object['max_at_once'], db_object['dodo_code'],
                       db_object['island_name'], db_object['is_locked'], db_object['join_code'], int(db_object['channel_id']), int(db_object['roster_message_id']))
    
    @staticmethod
    def get_all_queues():
        db = Database()
        
        queues = []
        for queue in db.queues.fetchAll():
            queues.append(VHQueue.create_queue_from_db_obj(queue))
        
        def queue_sort_value(queue):
            return len(queue.get_members())

        return sorted(queues, key=queue_sort_value)
    
    @staticmethod
    def get_queue_by_join_code(join_code: str):
        db = Database()

        aql_query = 'FOR q IN queues FILTER q.join_code == "{0}" RETURN q'.format(join_code)
        aql_result = db.db.AQLQuery(aql_query, rawResults=True)
        if len(aql_result) == 0:
            return None
        
        queue = aql_result[0]
        return VHQueue.create_queue_from_db_obj(queue)
    
    @staticmethod
    def get_queue_by_channel_id(channel_id: int):
        db = Database()

        aql_query = 'FOR q in queues FILTER q.channel_id == "{0}" RETURN q'.format(channel_id)
        aql_result = db.db.AQLQuery(aql_query, rawResults=True)
        if len(aql_result) == 0:
            return None
        
        queue = aql_result[0]
        return VHQueue.create_queue_from_db_obj(queue)
    
    @staticmethod
    def get_queue_by_member(user_id: int):
        db = Database()

        aql_query = 'FOR q IN queues FILTER "{0}" IN q.members RETURN q'.format(user_id)
        aql_result = db.db.AQLQuery(aql_query, rawResults=True)
        if len(aql_result) == 0:
            return None
        
        queue = aql_result[0]

        return VHQueue.create_queue_from_db_obj(queue)
    
    @staticmethod
    def get_queue_by_owner(owner_id: int):
        db = Database()

        if not str(owner_id) in db.queues:
            return None

        queue = db.queues[str(owner_id)]
        
        return VHQueue.create_queue_from_db_obj(queue)
    
    @staticmethod
    def is_user_in_any_queue(user_id: int):
        return not VHQueue.get_queue_by_member(user_id) is None
    
    def add_member(self, user_id: int):
        if self.has_member(user_id):
            return
        
        queue = self.get_queue_db_object()

        if queue['members'] is None:
            queue['members'] = []
        queue['members'].append(str(user_id))
        queue.save()
    
    def close(self):
        self.lock()
        
        all_members = self.get_members()
        active_members = self.get_active_members()
        for member in all_members:
            if not member in active_members:
                self.remove_member(member)
    
    def end(self):
        queue = self.get_queue_db_object()
        queue.delete()
    
    def has_member(self, user_id: int):
        return user_id in self.get_members()

    def is_open(self):
        return (not self.is_locked and
                self.get_queue_size() < self.max_size)
    
    def get_active_members(self):
        return self.get_members()[0:self.max_at_once]

    def get_formatted_dodo(self):
        return ' '.join(self.dodo_code.upper())
    
    def get_members(self):
        queue = self.get_queue_db_object()
        members = queue['members']
        if members is None:
            return []
        else:
            return [int(x) for x in queue['members']]
    
    def get_queue_db_object(self):
        db = Database()

        queue = db.queues.fetchDocument(str(self.owner_id))
        return queue
    
    def get_queue_name(self):
        return 'queue-{0}'.format(self.join_code)
    
    def get_queue_size(self):
        return len(self.get_members())
    
    def lock(self):
        if self.is_locked:
            return
        
        queue = self.get_queue_db_object()
        queue['is_locked'] = True
        queue.save()

        self.is_locked = True
    
    def set_channel_id(self, channel_id: int):
        queue = self.get_queue_db_object()
        queue['channel_id'] = str(channel_id)
        queue.save()
        self.channel_id = channel_id
    
    def set_roster_message_id(self, roster_message_id: int):
        queue = self.get_queue_db_object()
        queue['roster_message_id'] = str(roster_message_id)
        queue.save()
        self.roster_message_id = roster_message_id
    
    def set_dodo(self, dodo: str):
        queue = self.get_queue_db_object()
        queue['dodo_code'] = dodo
        queue.save()
        self.dodo_code = dodo
    
    def remove_member(self, user_id: int):
        if not self.has_member(user_id):
            return
        
        queue = self.get_queue_db_object()
        queue['members'] = [member for member in queue['members'] if member != str(user_id)]
        queue.save()
    
    def unlock(self):
        if not self.is_locked:
            return
        
        queue = self.get_queue_db_object()
        queue['is_locked'] = False
        queue.save()

        self.is_locked = False
