import pytest

import os

from database import Database

class TestDatabase():
    # This scenario initializes the database, so run it first.
    @pytest.mark.order(1)
    def test_create_file(self):
        try:
            db = Database(init=True)
        except Exception as e:
            assert False, f"'test_create_file' raised an exception: {e}"

    def test_create_connection_failed(self):
        with pytest.raises(RuntimeError):
            Database(file='tests/resources/dbconfig_connection_failed.json')

    def test_create_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Database(file='does-not-exist')
    
    def test_create_invalid_data(self):
        with pytest.raises(ValueError):
            Database(file='tests/resources/dbconfig_invalid_data.json')

    def test_create_malformed_json(self):
        with pytest.raises(Exception):
            Database(file='tests/resources/dbconfig_malformed.json')

    def test_create_missing_data(self):
        with pytest.raises(ValueError):
            Database(file='tests/resources/dbconfig_missing_data.json')

    def test_create_missing_key(self):
        with pytest.raises(KeyError):
            Database(file='tests/resources/dbconfig_missing_keys.json')

    def test_create_nonexistent_db(self):
        with pytest.raises(KeyError):
            Database(file='tests/resources/dbconfig_nonexistent_db.json')

    def test_collections_exist(self):
        db = Database()
        required_collections = ['Redemptions', 'Members', 'Settings', 'Awards']

        assert all(map(lambda x: db.db.hasCollection(x), required_collections))