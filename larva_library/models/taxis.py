from mongokit import Document
from larva_library import db
from mongokit import OR

class Taxis(Document):
    __collection__= 'taxis'
    use_dot_notation = True
    structure = {
        'variable'      : unicode,
        'units'         : unicode,
        'min'           : OR(int, float),
        'max'           : OR(int, float),
        'gradient'      : OR(int, float)
    }
    def to_data(self):
        data = {}
        data['variable'] = self.variable
        data['units'] = self.units
        data['min'] = float(self.min)
        data['max'] = float(self.max)
        data['gradient'] = float(self.gradient)
        return data

    def __str__(self):
        return "%s (%s): %f -> %f +/- %f" % (self.variable, self.units, self.min, self.max, self.gradient)
db.register([Taxis])