from mongokit import Document
from larva_library import db

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