import json
import os.path
import requests

class Villager:
    def __init__(self, internal_id: str, name_en: str):
        self.internal_id = internal_id
        self.name_en = name_en
    
    @staticmethod
    def create_json_if_not_exists():
        if not os.path.exists('villagers.json'):
            # download from NHSE github
            response = requests.get('https://raw.githubusercontent.com/kwsch/NHSE/master/NHSE.Core/Resources/text/en/text_villager_en.txt')
            if not response.status_code == 200:
                raise AttributeError('Missing villagers.json and could not create')
            
            villagers = {}
            for line in response.split('\n'):
                internal_id, villager_name = line.split('\t')
                villagers[internal_id] = villager_name
            
            with open('villagers.json', 'w') as f:
                f.write(json.dumps(villagers))

    @staticmethod
    def get_by_name(name: str):
        special_mapping = {
            'Crackle': 'Spork',
            'Jakey': 'Jacob'
        }

        Villager.create_json_if_not_exists()

        if name.title() in special_mapping:
            name_en = special_mapping[name]
        else:
            name_en = name.title()
        
        with open('villagers.json', 'r') as f:
            all_villager_data = json.load(f)
        
        for internal_id in all_villager_data:
            villager_name = all_villager_data[internal_id]
            if villager_name == name_en:
                return Villager(internal_id, villager_name)
        
        return None
    
    @staticmethod
    def get_by_id(internal_id: str):
        Villager.create_json_if_not_exists()

        with open('villagers.json', 'r') as f:
            all_villager_data = json.load(f)

        try:
            return all_villager_data[internal_id]
        except KeyError:
            return None