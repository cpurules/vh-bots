import time

from pyArango.theExceptions import DocumentNotFoundError
from database import Database
from enum import Enum
from villager import Villager

class RequestStatus(Enum):
    UNAVAILABLE = 1
    AVAILABLE = 2
    COMPLETED = 3
    TIMEOUT = 4

    @staticmethod
    def from_str(label: str):
        if label.startswith('RequestStatus.'):
            label = label.split('.')[1]
        if label.upper() == 'UNAVAILABLE':
            return RequestStatus.UNAVAILABLE
        elif label.upper() == 'AVAILABLE':
            return RequestStatus.AVAILABLE
        elif label.upper() == 'COMPLETED':
            return RequestStatus.COMPLETED
        elif label.upper() == 'TIMEOUT':
            return RequestStatus.TIMEOUT
        else:
            raise NotImplementedError('Unknown request status: ' + label)

class Request:
    def __init__(self, _key: int, member_id: int, villager_name: str, submitted_timestamp: int, 
                    status: RequestStatus, was_accepted: bool = False, accepted_by: int = None,
                    accepted_timestamp: int = None, closed_timestamp: int = None):
        self._key = _key
        self.member_id = int(member_id)
        self.villager_name = villager_name
        self.submitted_timestamp = submitted_timestamp
        self.status = status
        self.was_accepted = was_accepted
        self.accepted_by = accepted_by
        self.accepted_timestamp = accepted_timestamp
        self.closed_timestamp = closed_timestamp
    
    @staticmethod
    def create_new_request(member_id: int, villager: Villager):
        db = Database()
        requests = db.requests

        item = requests.createDocument()
        item['member_id'] = str(member_id)
        item['villager_name'] = villager.name_en
        item['submitted_timestamp'] = int(time.time())
        item['status'] = RequestStatus.UNAVAILABLE
        item['was_accepted'] = False
        item.save()

        return Request.get_current_user_request(member_id)
    
    @staticmethod
    def create_request_from_db_obj(db_obj):
        request_fields = {
            '_key': int(db_obj['_key']),
            'member_id': int(db_obj['member_id']),
            'villager_name': db_obj['villager_name'],
            'submitted_timestamp': db_obj['submitted_timestamp'],
            'status': RequestStatus.from_str(db_obj['status']),
            'was_accepted': db_obj['was_accepted']
        }
        if db_obj['was_accepted']:
            request_fields['accepted_by'] = int(db_obj['accepted_by'])
            request_fields['accepted_timestamp'] = db_obj['accepted_timestamp']
            if request_fields['status'] in [RequestStatus.COMPLETED, RequestStatus.TIMEOUT]:
                request_fields['closed_timestamp'] = db_obj['closed_timestamp']
        
        return Request(**request_fields)
    
    @staticmethod
    def get_current_user_request(member_id: int):
        db = Database()

        query = 'FOR r IN requests FILTER r.member_id == "{0}" AND r.status IN ["{1}","{2}"] RETURN r'.format(member_id, RequestStatus.UNAVAILABLE, RequestStatus.AVAILABLE)
        result = db.db.AQLQuery(query)
        if len(result) == 0:
            return None
        else:
            return Request.create_request_from_db_obj(result[0])

    def change_villager(self, villager: Villager):
        request = self.get_request_db_obj()
        request['villager_name'] = villager.name_en
        request.save()

        self.villager_name = villager.name_en

    def get_request_db_obj(self):
        db = Database()

        return db.requests.fetchDocument(str(self._key))