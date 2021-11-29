from pyArango.theExceptions import DocumentNotFoundError
from database import Database

class Redemption:   
    def __init__(self, redemption_key: str, redemption_name: str, redemption_cost: int, redemption_enabled: bool, redemption_count: int):
        self._key = redemption_key
        self.name = redemption_name
        self.cost = redemption_cost
        self.enabled = redemption_enabled
        self.redemption_count = redemption_count
    
    def __str__(self):
        text = "{0} - {1} points".format(self.name, self.cost)
        if not self.enabled:
            text = text + " (DISABLED)"
        return text
    
    #staticmethod
    def cost_then_name_sorter(redemption):
        return (redemption.cost, redemption.name)
    
    #staticmethod
    def reverse_cost_then_name_sorter(redemption):
        return (-redemption.cost, redemption.name)
    
    #staticmethod
    def create_redemption(redemption_name: str, redemption_cost: int, redemption_enabled: bool):
        db = Database()
        redemptions = db.redemptions

        redemption_count = 0

        item = redemptions.createDocument()
        item['name'] = redemption_name
        item['cost'] = int(redemption_cost)
        item['enabled'] = bool(redemption_enabled)
        item['redemption_count'] = redemption_count
        item.save()

        return Redemption(item._key, redemption_name, redemption_cost, redemption_enabled, redemption_count)
    
    #staticmethod
    def create_redemption_from_db_obj(db_obj):
        return Redemption(db_obj['_key'], db_obj['name'], db_obj['cost'], db_obj['enabled'], db_obj['redemption_count'])
    
    #staticmethod
    def get_all_redemptions(sorter=None):
        db = Database()
        redemptions = []
        for redemption in db.redemptions.fetchAll():
            redemptions.append(Redemption.create_redemption_from_db_obj(redemption))
        if not sorter is None:
            redemptions.sort(key=sorter)
        return redemptions
    
    #staticmethod
    def get_redemption_by_key(redemption_key: str):
        db = Database()

        try:
            return Redemption.create_redemption_from_db_obj(db.redemptions[str(redemption_key)])
        except (KeyError, DocumentNotFoundError):
            return None
    
    # staticmethod
    def remove_redemption_by_key(redemption_key: str):
        db = Database()

        try:
            db.redemptions[str(redemption_key)].delete()
        except (KeyError, DocumentNotFoundError):
            raise DocumentNotFoundError('Unable to find redemption with specified key: {0}'.format(redemption_key))
    
    def get_redemption_db_object(self):
        db = Database()

        return db.redemptions.fetchDocument(str(self._key))
    
    def purchased(self):
        reward = self.get_redemption_db_object()
        reward['redemption_count'] += 1
        reward.save()
        self.redemption_count += 1

    def set_name(self, name: str):
        reward = self.get_redemption_db_object()
        reward['name'] = name
        reward.save()
        self.name = name
    
    def set_cost(self, cost: int):
        reward = self.get_redemption_db_object()
        reward['cost'] = int(cost)
        reward.save()
        self.cost = int(cost)
    
    def enable(self):
        reward = self.get_redemption_db_object()
        reward['enabled'] = True
        reward.save()
        self.enabled = True
    
    def disable(self):
        reward = self.get_redemption_db_object()
        reward['enabled'] = False
        reward.save()
        self.enabled = True