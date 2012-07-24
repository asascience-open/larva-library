from mongokit import Document, DocumentMigration
from larva_library import db, app
from wtforms import *
from datetime import datetime

class Diel(Document):
    __collection__= 'diel'
    use_dot_notation = True
    structure = {
        'type'          : unicode,
        'time'          : datetime,
        'cycle'         : unicode,
        'plus_or_minus' : unicode,
        'hours'         : int,
        'min'           : float,
        'max'           : float
    }
    def __str__(self):
        if self.type == "cycles":
            return "At %s %s%i hour(s): Move towards %dm -> %dm" % (self.cycle, self.plus_or_minus, self.hours, self.min, self.max)
        elif self.type == "specifictime":
            if self.time is not None:
                t = self.time.strftime("%H:%M UTC")
            else:
                t = None
            return "At %s: Move towards %dm -> %dm" % (t, self.min, self.max)
        else:
            return "No known type defined"
db.register([Diel])

class Taxis(Document):
    __collection__= 'taxis'
    use_dot_notation = True
    structure = {
        'variable'      : unicode,
        'units'         : unicode,
        'min'           : float,
        'max'           : float,
        'gradient'      : float
    }
    def __str__(self):
        return "%s (%s): %d -> %d +/- %d" % (self.variable, self.units, self.min, self.max, self.gradient)
db.register([Taxis])

class LifeStage(Document):
    __collection__= 'lifestage'
    use_dot_notation = True
    use_autorefs = True
    structure = {
        'name'      : unicode,
        'vss'       : float,
        'duration'  : int,
        'diel'      : [Diel],
        'taxis'     : [Taxis],
    }
db.register([LifeStage])

class Library(Document):
    __collection__= 'libraries'
    required_fields = ['name', 'user']
    indexes = [{'fields' : 'name', 'unique' : True}]
    use_dot_notation = True
    use_autorefs = True
    structure = {
        'name'          : unicode,
        'genus'         : unicode,
        'species'       : unicode,
        'common_name'   : unicode,
        'keywords'      : [unicode],
        'geo_keywords'  : [unicode],
        'geometry'      : unicode,
        'lifestages'    : [LifeStage],
        'user'          : unicode,
        'created'       : datetime,
        'status'        : unicode,
        '_keywords'     : [unicode]
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
    user_owned = BooleanField('User Owned Only')

## forms for library wizard (editing and creating)
class BaseWizard(Form):
    name = TextField('Name')
    genus = TextField('Genus')
    species = TextField('Species')
    common_name = TextField('Common Name')
    keywords = TagListField('Keywords')
    geo = HiddenField('Geo');
    geo_keywords = TagListField('Geographical Keywords')
    status = SelectField('Permissions', choices=[('private', 'Private'), ('public', 'Public'), ('review', 'Under Review')])

## forms for library wizard (editing and creating)
class LifeStageWizard(Form):
    name = TextField('Name')
    vss = FloatField('Vertical Swimming Speed (m/s)')
    duration = IntegerField('Lifestage Duration (days)')

    diel = BooleanField('Diel')
    taxis = BooleanField('Sensory')

    diel_hours = FloatField("", [validators.optional()])
    diel_min_depth = FloatField("Min", [validators.optional()])
    diel_max_depth = FloatField("Max", [validators.optional()])
    diel_data = HiddenField('diel_data')

    taxis_min = FloatField("Min", [validators.optional()])
    taxis_max = FloatField("Max", [validators.optional()])
    taxis_grad = FloatField("Sensory Gradient +/-", [validators.optional()])
    taxis_data = HiddenField('taxis_data')