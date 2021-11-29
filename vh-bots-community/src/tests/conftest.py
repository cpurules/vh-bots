import pytest

from database import Database

@pytest.fixture(scope='module', autouse=True)
def initialize_database():
    db = Database(init=True)

@pytest.fixture(scope='function')
def import_redemption_data():
    db = Database()
    db.redemptions.truncate()
    db.redemptions.bulkImport_json(filename='tests/resources/redemptions.json')

@pytest.fixture(scope='function')
def import_member_data():
    db = Database()
    db.members.truncate()
    db.members.bulkImport_json(filename='tests/resources/members.json')