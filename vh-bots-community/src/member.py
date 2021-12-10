from pyArango.theExceptions import DocumentNotFoundError
from database import Database
from award import Award
from redemption import Redemption

class GuildMember:   
    def __init__(self, member_id: int, member_balance: int):
        self._key = int(member_id)
        self.balance = int(member_balance)
    
    @staticmethod
    def create_member(member_id: int, member_balance: int=500):
        db = Database()
        members = db.members

        item = members.createDocument()
        item['_key'] = str(member_id)
        item['balance'] = int(member_balance)
        item.save()

        return GuildMember(member_id, member_balance)
    
    @staticmethod
    def create_member_from_db_obj(db_obj):
        return GuildMember(db_obj['_key'], db_obj['balance'])
    
    @staticmethod
    def get_member_by_id(member_id: int):
        db = Database()

        try:
            return GuildMember.create_member_from_db_obj(db.members[str(member_id)])
        except (KeyError, DocumentNotFoundError):
            return None
    
    # staticmethod
    def remove_member_by_id(member_id: int):
        db = Database()

        try:
            db.members[str(member_id)].delete()
        except (KeyError, DocumentNotFoundError):
            raise DocumentNotFoundError("Unable to find member with specified ID", member_id)
    
    def adjust_balance(self, delta: int):
        self.set_balance(self.balance + delta)
    
    def can_purchase(self, reward: Redemption):
        return self.balance >= reward.cost

    def get_member_db_object(self):
        db = Database()

        return db.members.fetchDocument(str(self._key))
    
    def get_mention(self):
        return "<@{0}>".format(self._key)
    
    def process_award(self, award: Award):
        if not award.member_id == self._key:
            raise ValueError("Can only process Awards for themselves")

        self.adjust_balance(award.points)
    
    def purchase(self, reward: Redemption):
        if not self.can_purchase(reward):
            raise PermissionError("Balance too low to purchase this reward")
        self.adjust_balance(-1 * reward.cost)

    def set_balance(self, balance: int):
        if balance < 0:
            raise ValueError("Cannot set to a negative balance", balance)
        
        member = self.get_member_db_object()
        member['balance'] = int(balance)
        member.save()
        self.balance = balance