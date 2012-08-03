from mongokit import Document, DocumentMigration
from larva_library import db, app
from wtforms import *
from datetime import datetime
import json

class Capability(Document):
    __collection__ = 'capability'
    use_dot_notation = True
    structure = {
        'vss'               : float,
        'variance'          : float,
        'swim_turning'      : unicode,
        'nonswim_turning'   : unicode
    }
db.register([Capability])

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
        try:
            data['diel_time'] = self.time.strftime("%H") + ":00"
            data['timezone'] = self.time.strftime("%z")
        except:
            data['diel_time'] = None
            data['timezone'] = None
        data['cycle'] = self.cycle;
        data['plus_or_minus'] = self.plus_or_minus
        data['hours'] = self.hours
        data['min'] = self.min
        data['max'] = self.max
        return data

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
        return data

    def __str__(self):
        return "%s (%s): %d -> %d +/- %d" % (self.variable, self.units, self.min, self.max, self.gradient)
db.register([Taxis])

class LifeStage(Document):
    __collection__= 'lifestage'
    use_dot_notation = True
    use_autorefs = True
    structure = {
        'name'      : unicode,
        'duration'  : int,
        'linear_a'  : float,
        'linear_b'  : float,
        'diel'      : [Diel],
        'taxis'     : [Taxis],
        'capability': Capability,
        'notes'     : unicode
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
        'notes'         : unicode,
        '_keywords'     : [unicode]
    }
    
    STATUS_PUBLIC  = "public"
    STATUS_REVIEW  = "review"
    STATUS_PRIVATE = "private"
    STATUS_DEPREC  = "deprecated"

    def ensure_unique(self):
        name = self['name']
        name_num = 1
        while self.local_validate() is False:
            self['name'] = ("%s%d") % (name, name_num)
            name_num += 1

    def local_validate(self):
        # this will not call the super.validate()
        # this version is necessary because super.validate() requires that the document has an _id, which isn't necessarily true
        query = {'user': self['user'], 'name': self['name']}
        entry = db.Library.find_one(query)
        if entry is not None:
            try:
                if entry['_id'] != self['_id']:
                    return False
            except:
                return False
        return True


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
        self._keywords = list(set(_keywords))
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
    status = SelectField('Permissions', choices=[(Library.STATUS_PRIVATE, 'Private'), (Library.STATUS_PUBLIC, 'Public'), (Library.STATUS_REVIEW, 'Under Review'), (Library.STATUS_DEPREC, "Deprecated")])
    notes = TextAreaField('Notes')

## forms for library wizard (editing and creating)
class LifeStageWizard(Form):
    name = TextField('Name')
    duration = IntegerField('Lifestage Duration (days)')
    linear = BooleanField("")
    linear_a = FloatField("A", [validators.optional()])
    linear_b = FloatField("B", [validators.optional()])
    notes = TextAreaField('Notes')

    diel = BooleanField('Diel')
    taxis = BooleanField('Sensory')
    capability = BooleanField('Capability')

    # Diel
    diel_hours = FloatField("", [validators.optional()])
    diel_min_depth = FloatField("Min", [validators.optional()])
    diel_max_depth = FloatField("Max", [validators.optional()])
    diel_data = HiddenField('diel_data')

    # Capability
    vss = FloatField('Vertical Swimming Speed (m/s)')
    variance = FloatField('Swimming Speed Variance (m/s)', default=0)
    swim_turning = RadioField("", [validators.optional()], choices=[('reverse', 'Reverses swimming direction'), ('random', 'Random selection of swimming direction')])
    nonswim_turning = RadioField("", [validators.optional()], choices=[('random', 'Random selection of swimming direction'), ('downward', 'Always swim downward'), ('upward', 'Always swim updard')])

    # Taxis
    variable = SelectField('Variable', [validators.optional()], choices=[('sea_water_salinity', 'Salinity (PSU)'), ('sea_water_temperature', 'Temperature (deg C)')])
    taxis_min = FloatField("Min", [validators.optional()])
    taxis_max = FloatField("Max", [validators.optional()])
    taxis_grad = FloatField("Sensory Gradient +/-", [validators.optional()])
    taxis_data = HiddenField('taxis_data')