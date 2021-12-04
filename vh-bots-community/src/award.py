from database import Database
from datetime import datetime, timedelta

class Award:
    def __init__(self, _key: str, message: int, author: int, link: str, queued_at: datetime, points: int, deleted: bool=False, awarded_at: datetime=None):
        self._key = _key
        self.message = message
        self.author = author
        self.link = link
        self.queued_at = queued_at
        self.awarded_at = awarded_at
        self.points = points
        self.deleted = deleted
    
    def __str__(self):
        msg = "Post by {0} {1} at {2} - {3} points{4}"
        if not self.deleted:
            msg_desc = "\[[jump to post]({0})\]".format(self.link)
        else:
            msg_desc = "\[deleted\]"

        time_formatted = self.queued_at.strftime('%d-%b-%Y %I:%M%p')

        if self.deleted:
            trail = ""
        elif self.awarded_at is None:
            trail = " (pending)"
        else:
            trail = " (awarded)"

        return msg.format("<@{0}>".format(self.author), msg_desc, time_formatted, self.points, trail)

    #staticmethod
    def create_award_from_db_obj(db_obj):
        def strptime(dt: str):
            return datetime.strptime(dt[:26], '%Y-%m-%d %H:%M:%S.%f')

        awarded_at = None if not 'awarded_at' in db_obj or db_obj['awarded_at'] is None else strptime(db_obj['awarded_at'])

        return Award(db_obj['_key'], int(db_obj['message']), int(db_obj['author']), db_obj['link'], strptime(db_obj['queued_at']),
                        db_obj['points'], db_obj['deleted'], awarded_at=awarded_at)
    
    #staticmethod
    def count_user_awards(user: int, past_hours: int=None):
        db = Database()

        now = datetime.now()
        if not past_hours is None:
            time_delta = timedelta(hours=past_hours)
            time_boundary = now - time_delta
        else:
            time_boundary = 0

        aql_query = "FOR a IN awards FILTER a.author == '{0}' AND a.queued_at > '{1}' RETURN a".format(user, time_boundary)
        aql_results = db.db.AQLQuery(aql_query, rawResults=True)
        return len(aql_results)

    #staticmethod
    def get_queued_awards(before: datetime=None):
        db = Database()
        
        awards = []

        query = "FOR award IN awards SORT award.queued_at DESC FILTER "
        if not before is None:
            query = query + "award.queued_at < '{0}' && ".format(before)
        query = query + "NOT award.deleted && award.awarded_at == NULL RETURN award"

        db_results = db.db.AQLQuery(query, rawResults=True)
        if len(db_results) > 0:
            for result in db_results:
                awards.append(Award.create_award_from_db_obj(result))
        
        return awards

    #staticmethod
    def queue_new_award(message: int, author: int, link: int, points: int):
        db = Database()

        award_data = {
            'message': str(message),
            'author': str(author),
            'link': str(link),
            'queued_at': datetime.now(),
            'points': points,
            'deleted': False
        }

        db_award = db.awards.createDocument(award_data)
        db_award.save()

        return Award(db_award['_key'], message, author, link, db_award['queued_at'], points, False)
    
    def award(self):
        self.awarded_at = datetime.now()
        self.save()
    
    def mark_deleted(self):
        self.deleted = True
        self.save()
    
    def save(self):
        # This only saves mutable fields
        db = Database()

        db_obj = db.awards.fetchDocument(self._key)

        db_obj['queued_at'] = self.queued_at
        db_obj['awarded_at'] = self.awarded_at
        db_obj['deleted'] = self.deleted
        db_obj.save()
