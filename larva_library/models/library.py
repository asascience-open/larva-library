from flask.ext.mongokit import Document
from larva_library import db, app
from wtforms import Form, TextField, validators, IntegerField, Field, FieldList, FormField, BooleanField, HiddenField
from wtforms import widgets
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
        'Geometry'   : [unicode],
        'Lifestages' : [{
            'name' : unicode,
            'stage': int
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

# sub-forms
class LifestageForm(Form):
    name = TextField('StageName')

## forms for library searching
class LibrarySearch(Form):
    search_keywords = TextField('Keywords')
    user_owned = BooleanField('User_Owned_Only')

## forms for library wizard (editing and creating)
class WizardFormOne(Form):
    lib_name = TextField('Name', [validators.Length(max=128)])
    genus = TextField('Genus')
    species = TextField('Species')
    common_name = TextField('Common_Name')
    
class WizardFormTwo(Form):
    # using the taglistfield demostrated from wtforms.simplecodes.com
    keywords = TagListField('Keywords')
    geo = HiddenField('Geo');
    geo_keywords = TagListField('Goegraphical Keywords')
    
class WizardFormThree(Form):
    # display the number of life stages based on the number input for number_of_lifestages
    lifestages = FieldList(FormField(LifestageForm))
            
    