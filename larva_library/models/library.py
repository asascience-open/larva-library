from flask.ext.mongokit import Document
from larva_library import db, app
from wtforms import *
from datetime import datetime
#import datetime
#
##document class
class Library(Document):
    __collection__= 'libraries'
    required_fields = ['name', 'user']
    indexes = [{'fields' : 'name', 'unique' : True}]
    use_dot_notation = True
    structure = {
        'name'       : unicode,
        'genus'      : unicode,
        'species'    : unicode,
        'common_name': unicode,
        'keywords'   : [unicode],
        'geo_keywords': [unicode],
        'geometry'   : unicode,
        'lifestages' : [{
            'name'      : unicode,
            'vss'       : float,
            'duration'  : int
        }],
        'user'       : unicode,
        'created'    : datetime,
        '_keywords'  : [unicode]
    }
    
    def __getstate__(self):
        result = self
        return result
    
    def copy_from_dictionary(self,dict=None):
        if dict is None:
            return self
        else:
            for key in dict.keys():
                if key in self.structure.keys():
                    self[key] = dict[key]
            return self
    
    def build_keywords(self):
        _keywords = []
        _keywords.extend(self.name.split(' '))
        _keywords.extend(self.genus.split(' '))
        _keywords.extend(self.species.split(' '))
        _keywords.extend(self.common_name.split(' '))
        _keywords.extend(self.keywords)
        _keywords.extend(self.geo_keywords)
        self._keywords = _keywords

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
    search_keywords = TextField('keywords')
    user_owned = BooleanField('User_Owned_Only')

## forms for library wizard (editing and creating)
class BaseWizard(Form):
    name = TextField('Name')
    genus = TextField('Genus')
    species = TextField('Species')
    common_name = TextField('Common Name')
    keywords = TagListField('Keywords')
    geo = HiddenField('Geo');
    geo_keywords = TagListField('Geographical Keywords')

## forms for library wizard (editing and creating)
class LifeStageWizard(Form):
    name = TextField('Name')
    vss = FloatField('Vertical Swimming Speed (m/s)')
    duration = IntegerField('Lifestage Duration (days)')

    diel = BooleanField('Diel')
    taxis = BooleanField('Sensory')

    diel_data = HiddenField('diel_data')
    taxis_data = HiddenField('taxis_data')