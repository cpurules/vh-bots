from pyArango.theExceptions import DocumentNotFoundError
from database import Database

class BotSetting:
    def __init__(self, area: str, token: str, display_name: str, value, description: str=None, value_cast=None):
        self.area = str(area)
        self.token = str(token)
        self.display_name = display_name
        self.value = value
        self.description = description
        
        if callable(value_cast):
            if isinstance(self.value, list):
                self.value = [value_cast(x) for x in self.value]
            else:
                self.value = value_cast(self.value)

    def get_setting_path(self):
        return "vh-community-bot;{0};{1}".format(self.area, self.token)

    def has_description(self):
        return not self.description is None and not self.description == ""

    def is_complex(self):
        return type(self.value) in [list, dict]
    
    def is_simple_list(self):
        # technically this will return true for empty complex lists
        # however this is only used in settings_cog.py after we already check for complex list settings
        # so it's okay and fixes the issue of an empty complex list throwing an IndexError
        return isinstance(self.value, list) and (len(self.value) == 0 or not type(self.value[0]) in [list, dict])
    
    def save(self, overwrite: bool=False, value_cast=None):
        value = self.value
        if isinstance(value, list) and callable(value_cast):
            value = [value_cast(x) for x in value]

        try:
            setting = Database().settings.fetchDocument(self.get_setting_path())
            if not overwrite:
                raise AttributeError("Config setting already exists and overwrite is set to False")
        except DocumentNotFoundError:
            setting = Database().settings.createDocument({'_key': self.get_setting_path()})
        
        setting['display_name'] = self.display_name
        setting['value'] = value
        if not self.description is None and not self.description == '':
            setting['description'] = self.description
        
        setting.save()
    
    def value_str(self):
        if not type(self.value) in [list, dict]:
            return str(self.value)
        elif isinstance(self.value, list):
            first = self.value[0]
            if type(first) in [list, dict]:
                return '[...]'
            else:
                return "[{0}]".format(', '.join([str(x) for x in self.value]))
        else:
            return '...'

class BotSettingBuilder:
    def __init__(self):
        self.area = None
        self.token = None
        self.display_name = None
        self.description = None
        self.value = None
    
    def setArea(self, area: str):
        if area is None or str(area) == "":
            raise ValueError("Area must be specified")
        elif self.area is not None:
            raise AttributeError("Area is already set to {0}".format(self.area))

        self.area = str(area)
        return self

    def setToken(self, token: str):
        if token is None or str(token) == "":
            raise ValueError("Setting must be specified")
        elif self.token is not None:
            raise AttributeError("Token is already set to {0}".format(self.token))
        
        self.token = str(token)
        return self
    
    def setDisplayName(self, display_name: str):
        if display_name is None or str(display_name) == "":
            raise ValueError("Display name must be specified")
        elif self.display_name is not None:
            raise AttributeError("Display name is already set to {0}".format(self.display_name))
        
        self.display_name = str(display_name)
        return self
    
    def setDescription(self, description: str):
        if description is None or str(description) == "":
            raise ValueError("Description must be specified")
        elif self.description is not None:
            raise AttributeError("Description is already set to {0}".format(self.description))
        
        self.description = str(description)
        return self
    
    def setValue(self, value):
        if value is None:
            raise ValueError("Value must be specified")
        elif self.value is not None:
            raise AttributeError("Value is already set to {0}".format(self.value))
        
        self.value = value
        return self
    
    def build(self):
        if self.area is None or self.token is None or self.display_name is None or self.value is None:
            raise AttributeError("Missing at least one required attribute for setting")
        
        return BotSetting(self.area, self.token, self.display_name, self.value, self.description)

class BotSettings:
    #staticmethod
    def get_setting(area: str, token: str, value_cast=None):
        try:
            setting = Database().settings.fetchDocument('vh-community-bot;{0};{1}'.format(area, token))
            if not 'description' in setting:
                setting['description'] = None
            return BotSetting(area, token, setting['display_name'], setting['value'], setting['description'], value_cast)
        except (DocumentNotFoundError, KeyError):
            raise DocumentNotFoundError("Unable to find configuration item {0}.{1}".format(area, token))
    
    #staticmethod
    def get_all_areas():
        areas = []
        aql_query = 'FOR s IN settings FILTER s._key LIKE "vh-community-bot;%" COLLECT area = SPLIT(s._key, ";")[1] RETURN { "area": area }'
        aql_results = Database().db.AQLQuery(aql_query, rawResults=True)
        return [result['area'] for result in aql_results]

    #staticmethod
    def get_all_area_settings(area: str):
        settings = {}
        aql_query = 'FOR s IN settings FILTER s._key LIKE "vh-community-bot;{0};%" RETURN s'.format(area)
        aql_results = Database().db.AQLQuery(aql_query, rawResults=True)
        
        for result in aql_results:
            token = result['_key'].split(';')[2]
            settings[token] = BotSettings.get_setting(area, token)
        
        return settings