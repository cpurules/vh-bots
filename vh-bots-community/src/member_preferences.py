from pyArango.theExceptions import DocumentNotFoundError
from database import Database

class MemberPreferences:
    def __init__(self, member_id: int, notify_on_award: bool):
        self._key = int(member_id)
        self.notify_on_award = notify_on_award
    
    @staticmethod
    def create_preferences(member_id: int, notify_on_award: bool=False):
        db = Database()
        preferences = db.member_preferences

        item = preferences.createDocument()
        item['_key'] = str(member_id)
        item['notify_on_award'] = notify_on_award
        item.save()

        return MemberPreferences(member_id, notify_on_award)
    
    @staticmethod
    def create_preferences_from_db_obj(db_obj):
        return MemberPreferences(db_obj['_key'], db_obj['notify_on_award'])
    
    @staticmethod
    def get_preferences_by_member_id(member_id: int):
        db = Database()

        try:
            return MemberPreferences.create_preferences_from_db_obj(db.member_preferences[str(member_id)])
        except (KeyError, DocumentNotFoundError):
            return None
    
    # staticmethod
    def remove_preferences_by_member_id(member_id: int):
        db = Database()

        try:
            db.member_preferences[str(member_id)].delete()
        except (KeyError, DocumentNotFoundError):
            raise DocumentNotFoundError("Unable to find preferences for member with specified ID", member_id)

    def get_db_object(self):
        db = Database()

        return db.member_preferences.fetchDocument(str(self._key))
    
    def save(self):
        # This only saves mutable fields
        db = Database()

        db_obj = db.member_preferences.fetchDocument(self._key)

        db_obj['notify_on_award'] = self.notify_on_award
        db_obj.save()