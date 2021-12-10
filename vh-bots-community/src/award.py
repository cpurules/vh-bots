from database import Database
from datetime import datetime, timedelta

class Award:
    time_format = '%d-%b-%Y %I:%M%p'

    def __init__(self, _key: str, member_id: int, points: int, awarded_at: datetime, source: str, *, \
                    gifted_by: int=None, gift_reason: str=None, \
                    message_id: int=None, message_link: str=None, is_pending: bool=None, deleted: bool=False):
        self._key = _key
        self.member_id = member_id
        self.points = points
        self.awarded_at = awarded_at
        self.source = source

        self.gifted_by = gifted_by
        self.gift_reason = gift_reason

        self.message_id = message_id
        self.message_link = message_link
        self.is_pending = is_pending
        self.deleted = deleted
    
    def __str__(self):
        trail = ""

        if self.source == "user":
            msg = "Gifted to {0} by {1}"
            msg_desc = "<@{0}>".format(self.gifted_by)
        elif self.source == "post":
            msg = "Post by {0} {1}"
        
            if not self.deleted:
                msg_desc = "\[[jump]({0})\]".format(self.message_link)
                if not self.is_pending:
                    trail = " (pending)"
                else:
                    trail = " (awarded)"    
            else:
                msg_desc = "\[deleted\]"

        msg += " at {2} - {3} points{4}"

        time_formatted = self.awarded_at.strftime(Award.time_format)

        return msg.format("<@{0}>".format(self.member_id), msg_desc, time_formatted, self.points, trail)

    @staticmethod
    def create_award_from_db_obj(db_obj):
        def strptime(dt: str):
            return datetime.strptime(dt[:26], '%Y-%m-%d %H:%M:%S.%f')
        
        kwargs = {}
        kwargs['_key'] = db_obj['_key']
        kwargs['member_id'] = int(db_obj['member_id'])
        kwargs['points'] = db_obj['points']
        kwargs['awarded_at'] = strptime(db_obj['awarded_at'])
        kwargs['source'] = db_obj['source']
        if kwargs['source'] == 'user':
            kwargs['gifted_by'] = int(db_obj['gifted_by'])
            kwargs['gift_reason'] = db_obj['gift_reason']
        elif kwargs['source'] == 'post':
            kwargs['message_id'] = int(db_obj['message_id'])
            kwargs['message_link'] = db_obj['message_link']
            kwargs['is_pending'] = db_obj['is_pending']
            kwargs['deleted'] = db_obj['deleted']

        return Award(**kwargs)
    
    @staticmethod
    def count_user_awards(user: int, past_hours: int=None):
        db = Database()

        now = datetime.now()
        if not past_hours is None:
            time_delta = timedelta(hours=past_hours)
            time_boundary = now - time_delta
        else:
            time_boundary = 0

        aql_query = "FOR a IN awards FILTER a.member_id == '{0}' AND a.awarded_at > '{1}' RETURN a".format(user, time_boundary)
        aql_results = db.db.AQLQuery(aql_query, rawResults=True)
        return len(aql_results)
    
    @staticmethod
    def get_user_award_history(member_id: int, max_count: int=None):
        db = Database()
        awards = []

        history_query = "FOR a IN awards FILTER a.member_id == '{0}' SORT a.awarded_at DESC ".format(member_id)
        if max_count is not None:
            history_query += "LIMIT {0} ".format(max_count)
        history_query += "RETURN a"

        award_history = db.db.AQLQuery(history_query, rawResults=True)
        for award in award_history:
            awards.append(Award.create_award_from_db_obj(award))
        
        return awards

    @staticmethod
    def get_queued_post_awards(before: datetime=None):
        db = Database()
        
        awards = []

        query = "FOR award IN awards SORT award.awarded_at DESC FILTER award.source == 'post' AND "
        if not before is None:
            query = query + "award.awarded_at < '{0}' AND ".format(before)
        query = query + "NOT award.deleted AND award.is_pending RETURN award"

        db_results = db.db.AQLQuery(query, rawResults=True)
        if len(db_results) > 0:
            for result in db_results:
                awards.append(Award.create_award_from_db_obj(result))
        
        return awards
    
    @staticmethod
    def new_gift_award(member_id: int, points: int, gifted_by: int, gift_reason: str):
        db = Database()

        award_data = {
            'member_id': str(member_id),
            'points': points,
            'awarded_at': datetime.now(),
            'source': 'user',
            'gifted_by': str(gifted_by),
            'gift_reason': gift_reason
        }

        db_award = db.awards.createDocument(award_data)
        db_award.save()
        db_award = db.awards.fetchDocument(db_award['_key'])

        return Award.create_award_from_db_obj(db_award)

    @staticmethod
    def new_post_award(member_id: int, points: int, message_id: int, message_link: str):
        db = Database()

        award_data = {
            'member_id': str(member_id),
            'points': points,
            'awarded_at': datetime.now(),
            'source': 'post',
            'message_id': str(message_id),
            'message_link': message_link,
            'is_pending': True,
            'deleted': False
        }

        db_award = db.awards.createDocument(award_data)
        db_award.save()
        db_award = db.awards.fetchDocument(db_award['_key'])

        return Award.create_award_from_db_obj(db_award)
    
    def process_award(self):
        if not self.source == 'post':
            raise ValueError('Only post awards are queued for later processing')
        elif not self.is_pending:
            raise ValueError('This award has already been processed')

        self.is_pending = False
        self.save()
    
    def mark_deleted(self):
        if not self.source == 'post' or self.deleted or not self.is_pending:
            raise ValueError('Only active, queued post awards can be marked as deleted')

        self.deleted = True
        self.save()
    
    def save(self):
        # This only saves mutable fields
        if not self.source == 'post':
            raise ValueError('Only post awards are mutable')

        db = Database()

        db_obj = db.awards.fetchDocument(self._key)
        db_obj['is_pending'] = self.is_pending
        db_obj['deleted'] = self.deleted
        db_obj.save()