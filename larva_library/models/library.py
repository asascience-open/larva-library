from mongokit import Document, DocumentMigration
from larva_library import db
from larva_library.utils import remove_mongo_keys
from larva_library.models.lifestage import LifeStage
from wtforms import *
from datetime import datetime
import json

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
        
    def simplified_json(self):
        tm = json.loads(self.to_json())
        remove_mongo_keys(tm)
        tm['_id'] = str(self._id)
        del(tm['lifestages'])
        del(tm['notes'])
        del(tm['keywords'])
        del(tm['geo_keywords'])
        return tm

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
    search_keywords = TextField('')
    user_owned = BooleanField('Restrict search to personal entries')

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
