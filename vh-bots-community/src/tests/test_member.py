from pyArango.theExceptions import DocumentNotFoundError
import pytest

from member import GuildMember
from database import Database

class TestGuildMember:
    def test_get_member(self, import_member_data):
        expected_key = 321472460019204097
        expected_balance = 1000000

        member = GuildMember.get_member_by_id(expected_key)
        assert (member is not None and
                member._key == expected_key and
                member.balance == expected_balance)

    def test_create(self, import_member_data):
        db = Database()

        expected_key = 350033568547733505
        expected_balance = 777

        member = GuildMember.create_member(expected_key, expected_balance)
        member_valid = (member._key == expected_key and
                        member.balance == expected_balance)
        
        expected_key = str(expected_key)
        try:
            member_db = db.members.fetchDocument(expected_key)
            member_db_valid = (member_db is not None and
                                member_db._key == expected_key and
                                member_db.balance == expected_balance)
        except (KeyError, DocumentNotFoundError):
            member_db_valid = False
        
        assert (member_valid and member_db_valid)
    
    def test_remove_member(self, import_member_data):
        remove_key = '495369994658381879'
        GuildMember.remove_member_by_id(remove_key)
        assert (GuildMember.get_member_by_id(remove_key) == None)
    
    def test_remove_nonexistent_member(self, import_member_data):
        remove_key = 'zzzz'
        with pytest.raises(DocumentNotFoundError):
            GuildMember.remove_member_by_id(remove_key)
    
    def test_set_balance(self, import_member_data):
        member_id = '337389162758144030'
        expected_balance = 420
        new_balance = 6969

        member = GuildMember.get_member_by_id(member_id)
        old_balance = member.balance

        member.set_balance(new_balance)

        assert (old_balance == expected_balance and
                member.balance == new_balance)
    
    def test_mention(self, import_member_data):
        member_id = '337389162758144030'
        expected_mention = '<@{0}>'.format(member_id)
        
        member = GuildMember.get_member_by_id(member_id)
        assert (member is not None and member.get_mention() == expected_mention)
