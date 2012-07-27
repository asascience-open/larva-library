from mongokit import Document, DocumentMigration
from larva_library import db, app
from wtforms import *
from datetime import datetime
from copy import deepcopy
import json

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
    def to_data(self):
        data = {}
        data['diel_type'] = self.type
        if self.time is not None:
            data['diel_time'] = self.time.strftime("%H")
            data['timezone'] = self.time.strftime("%z")

        data['cycle'] = self.cycle;
        data['plus_or_minus'] = self.plus_or_minus
        data['hours'] = self.hours
        data['min'] = self.min
        data['max'] = self.max
        return str(data)

    def clone(self):
        clone = deepcopy(self)
        remove_id(clone)
        return clone

    def save(self):
        # verify that we don't hav any excess items not in structure
        excess_list = [ key for key in self.keys() if key not in self.structure.keys() ]
        for item in excess_list:
            del self[item]
        super(Diel, self).save()

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
    def to_data(self):
        data = {}
        data['variable'] = self.variable
        data['units'] = self.units
        data['min'] = self.min
        data['max'] = self.max
        data['gradient'] = self.gradient
        return str(data)

    def clone(self):
        clone = deepcopy(self)
        remove_id(clone)
        return clone

    def save(self):
        # verify that we don't hav any excess items not in structure
        excess_list = [ key for key in self.keys() if key not in self.structure.keys() ]
        for item in excess_list:
            del self[item]
        super(Taxis, self).save()

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

    def copy_from_dictionary(self,dict_cp=None):
        if dict_cp is None:
            return self
        else:
            for key in dict_cp.keys():
                if key in self.structure.keys():
                    if isinstance(dict_cp[key], str):
                        self[key] = unicode(dict_cp[key])
                    else:
                        self[key] = dict_cp[key]
            return self

    def save(self):
        # sav sub-documents
        for diel in self.diel:
            diel.save()
        for taxis in self.taxis:
            taxis.save()
        # verify that we don't hav any excess items not in structure
        excess_list = [ key for key in self.keys() if key not in self.structure.keys() ]
        for item in excess_list:
            del self[item]

        super(LifeStage, self).save()

    def clone(self):
        clone = deepcopy(self)
        remove_id(clone)
        return clone

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
        if dict is not None:
            for key in dict.keys():
                if key in self.structure.keys():
                    if isinstance(dict[key], str):
                        self[key] = unicode(dict[key])
                    elif isinstance(dict[key], list):
                        if len(dict[key]) > 0 and isinstance(dict[key][0], str):
                            dict[key] = [ item.encode('utf_8') for item in dict[key] ]
                    else:
                        self[key] = dict[key]
        return self

    def ensure_unique(self):
        name = self['name']
        name_num = 1
        while self.local_validate() is False:
            self['name'] = ("%s%d") % (name, name_num)
            name_num += 1

    def clone(self):
        clone = deepcopy(self)
        remove_id(clone)
        return clone

    def save(self):
        # save lifestages
        for lifestage in self.lifestages:
            lifestage.save()
        # verify that we don't hav any excess items not in structure
        excess_list = [ key for key in self.keys() if key not in self.structure.keys() ]
        for item in excess_list:
            del self[item]

        super(Library, self).save()

    def local_validate(self):
        # this will not call the super.validate()
        # this version is necessary because super.validate() requires that the document has an _id, which isn't necessarily true
        query = {'user': self['user'], 'name': self['name']}
        entry = db.Library.find_one(query)
        if entry is not None:
            return False

    def validate(self, *args, **kwargs):
        query = {'user': self['user'], 'name': self['name']}
        entry = db.Library.find_one(query)
        if entry is not None:
            return False
        super(Library, self).validate(*args, **kwargs)
    
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
    search_keywords = TextField('Search Parameters (Comma-delimited)')
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


    variable = SelectField('Variable', choices=[('sea_water_salinity', 'Salinity (PSU)'), ('sea_water_temperature', 'Temperature (deg C)')])
    taxis_min = FloatField("Min", [validators.optional()])
    taxis_max = FloatField("Max", [validators.optional()])
    taxis_grad = FloatField("Sensory Gradient +/-", [validators.optional()])
    taxis_data = HiddenField('taxis_data')

def remove_id(item=None):
    if item is not None:
        if isinstance(item, list):
            for sub in item:
                remove_id(sub)
        elif isinstance(item, dict):
            for key in item.keys():
                remove_id(item[key])

        if isinstance(item, Document):
            if item.get('_id') is not None:
                del item['_id']

    return
