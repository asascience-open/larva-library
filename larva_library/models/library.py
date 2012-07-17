from flask.ext.mongokit import Document
from larva_library import db, app
from wtforms import *
from datetime import datetime
#import datetime
#
##document class
class Library(Document):
    __collection__= 'libraries'
    required_fields = ['Name']
    indexes = [{'fields' : 'Name', 'unique' : True}]
    use_dot_notation = True
    structure = {
        'Name'       : unicode,
        'Genus'      : unicode,
        'Species'    : unicode,
        'Common_Name': unicode,
        'Keywords'   : [unicode],
        'GeoKeywords': [unicode],
        'Geometry'   : unicode,
        'Lifestages' : [{
            'name'      : unicode,
            'vss'       : float,
            'duration'  : int
        }],
        'User'       : unicode,
        'Created'    : datetime,
        '_keywords'  : [unicode]
    }
    
    def __getstate__(self):
        result = self
        return result
    
    def copy_from_dictionary(self,dict=None):
        if dict is None or 'Name' not in dict.keys():
            return self
        else:
            for key in dict.keys():
                if key in self.structure.keys():
                    self[key] = dict[key]
            return self
    
db.register([Library])

# custom field classes
class TagListField(Field):
    widget = widgets.TextInput()
    
    def _value(self):
        if self.data:
            return u', '.join(self.data)
        else:
            return u''
        
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [x.strip() for x in valuelist[0].split(',')]
        else:
            self.data = []

## forms for library searching
class LibrarySearch(Form):
    search_keywords = TextField('Keywords')
    user_owned = BooleanField('User_Owned_Only')

## forms for library wizard (editing and creating)
class BaseWizard(Form):
    name = TextField('Name', [validators.Length(max=128)])
    genus = TextField('Genus')
    species = TextField('Species')
    common_name = TextField('Common_Name')
    keywords = TagListField('Keywords')
    geo = HiddenField('Geo');
    geo_keywords = TagListField('Goegraphical Keywords')

## forms for library wizard (editing and creating)
class LifeStageWizard(Form):
    name = TextField('Name', [validators.Length(max=128)])
    vss = FloatField('Vertical Swimming Speed (m/s)')
    duration = IntegerField('Lifestage Duration (days)')

    diel = BooleanField('Diel')
    taxis = BooleanField('Sensory')

    diel_data = HiddenField('diel_data')
    taxis_data = HiddenField('taxis_data')