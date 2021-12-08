import discord

from datetime import datetime

class EmbedBuilder:
    def __init__(self):
        self.title = None
        self.colour = None
        self.description= None
        self.fields = None
        self.timestamp = None
    
    @staticmethod
    def fromEmbed(embed):
        eb = EmbedBuilder()
        eb.title = embed.title
        eb.colour = embed.colour
        eb.description = embed.description
        if not embed.fields is None:
            eb.fields = [{'name': f.name, 'value': f.value, 'inline': f.inline} for f in embed.fields]
        eb.timestamp = embed.timestamp
        return eb
        
    def setTitle(self, title: str):
        if title.strip() == '':
            self.title = None
        else:
            self.title = str(title.strip())
        return self
    
    def setColour(self, colour):
        if colour is None:
            self.colour = None
        elif type(colour) in [tuple, list] and len(colour) == 3:
            # (R, G, B) or [R, G, B]
            self.colour = discord.Colour.from_rgb(*colour)
        else:
            raise TypeError("Unknown object passed", colour)
        return self
    
    def setDescription(self, description: str):
        if description.strip() == '':
            self.description = None
        else:
            self.description = str(description.strip())
        return self
    
    def setDescriptionFromLines(self, description_lines):
        if not type(description_lines) is list:
            raise TypeError("Unknown object passed", description_lines)
        if len(description_lines) == 0:
            self.description = None
        else:
            self.description = '\n'.join(description_lines)
        return self
    
    def appendToDescription(self, data):
        if not data is None:
            if not isinstance(data, list):
                data = [data]
            
            new_text = '\n'.join(data)
            if self.description is None:
                self.description = new_text
            else:
                self.description = '{0}\n{1}'.format(self.description, new_text)
        
        return self
    
    def addField(self, field):
        if not type(field) is dict:
            raise TypeError("Unknown object passed", field)
        if not 'name' in field or not 'value' in field:
            raise KeyError("Field object missing required key", field)
        
        if self.fields is None:
            self.fields = []
        if not 'inline' in field:
            field.update(inline=True)

        self.fields.append(field)
        return self
    
    def addSpacerField(self):
        if self.fields is None:
            self.fields = []
        self.fields.append({
            'name': '\u200B',
            'value': '\u200B',
            'inline': False
        })
        return self

    def clearFields(self):
        self.fields = None
        return self

    def setTimestamp(self, timestamp: datetime):
        self.timestamp = timestamp
        return self
    
    def build(self):
        embed = discord.Embed()
        if not self.title is None:
            embed.title = self.title
        if not self.colour is None:
            embed.colour = self.colour
        if not self.description is None:
            embed.description = self.description
        if not self.fields is None:
            for field in self.fields:
                embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        return embed