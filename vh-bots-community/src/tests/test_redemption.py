from pyArango.theExceptions import DocumentNotFoundError
import pytest

from redemption import Redemption

class TestRedemption:
    def test_get_redemption(self, import_redemption_data):
        expected_key = '2'
        expected_name = 'Second Redemption'
        expected_cost = 420
        expected_enabled = False
        expected_redemption_count = 9

        redemption = Redemption.get_redemption_by_key(expected_key)

        assert (redemption._key == expected_key and
                redemption.name == expected_name and
                redemption.cost == expected_cost and
                redemption.enabled == expected_enabled and
                redemption.redemption_count == expected_redemption_count)

    def test_create_and_get_redemption(self, import_redemption_data):
        expected_name = 'New Redeem'
        expected_cost = 300
        expected_enabled = False
        expected_redemption_count = 0

        redemption = Redemption.create_redemption(expected_name, expected_cost, expected_enabled)

        redemption_valid = (redemption.name == expected_name
                            and redemption.cost == 300
                            and redemption.enabled == expected_enabled
                            and redemption.redemption_count == expected_redemption_count)

        redemption_db = Redemption.get_redemption_by_key(redemption._key)

        redemption_db_valid = (redemption_db.name == expected_name
                                and redemption_db.cost == expected_cost
                                and redemption_db.enabled == expected_enabled
                                and redemption_db.redemption_count == expected_redemption_count)
        
        assert (redemption_valid and redemption_db_valid)
    
    def test_remove_redemption(self, import_redemption_data):
        remove_key = '3'
        Redemption.remove_redemption_by_key(remove_key)
        assert (Redemption.get_redemption_by_key(remove_key) == None)
    
    def test_remove_nonexistent_redemption(self, import_redemption_data):
        remove_key = 'zzzz'
        with pytest.raises(DocumentNotFoundError):
            Redemption.remove_redemption_by_key(remove_key)
    
    def test_sort_by_cost_then_name(self, import_redemption_data):
        expected_keys_order = ['6', '2', '5', '4', '3', '1']
        redemptions = Redemption.get_all_redemptions()
        redemptions.sort(key=Redemption.cost_then_name_sorter)
        assert [redemption._key for redemption in redemptions] == expected_keys_order
    
    def test_sort_by_cost_then_name_inline(self, import_redemption_data):
        expected_keys_order = ['6', '2', '5', '4', '3', '1']
        redemptions = Redemption.get_all_redemptions(sorter=Redemption.cost_then_name_sorter)
        assert [redemption._key for redemption in redemptions] == expected_keys_order
    
    def test_str_conversion_disabled(self, import_redemption_data):
        expected_str = "Last one baybee - 10 points (DISABLED)"
        redemption = Redemption.get_redemption_by_key('6')
        assert str(redemption) == expected_str
    
    def test_str_conversion_enabled(self, import_redemption_data):
        expected_str = "Test Redemption 1 - 1111 points"
        redemption = Redemption.get_redemption_by_key('1')
        assert str(redemption) == expected_str