import pytest

import os

from bot_config import BotConfig

class TestBotConfig():
    def test_create_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            BotConfig(config_file='does-not-exist')
    
    def test_create_invalid_data(self):
        with pytest.raises(ValueError):
            BotConfig(config_file='tests/resources/botconfig_invalid_data.json')

    def test_create_malformed_json(self):
        with pytest.raises(Exception):
            BotConfig(config_file='tests/resources/botconfig_malformed.json')

    def test_create_missing_data(self):
        with pytest.raises(ValueError):
            BotConfig(config_file='tests/resources/botconfig_missing_data.json')

    def test_create_missing_key(self):
        with pytest.raises(KeyError):
            BotConfig(config_file='tests/resources/botconfig_missing_keys.json')
    
    def test_create_file(self):
        try:
            config = BotConfig()
        except Exception as e:
            assert False, f"'test_create_file' raised an exception: {e}"