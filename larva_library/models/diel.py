from mongokit import Document
from larva_library import db
from datetime import datetime
from mongokit import OR

class Diel(Document):
    __collection__= 'diel'
    use_dot_notation = True
    structure = {
        'type'          : unicode,
        'time'          : datetime,
        'cycle'         : unicode,
        'plus_or_minus' : unicode,
        'hours'         : int,
        'min'           : OR(int, float),
        'max'           : OR(int, float)
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
            return "At %s %s%i hour(s): Move towards %fm -> %fm" % (self.cycle, self.plus_or_minus, self.hours, self.min, self.max)
        elif self.type == "specifictime":
            if self.time is not None:
                t = self.time.strftime("%H:%M UTC")
            else:
                t = None
            return "At %s: Move towards %dm -> %dm" % (t, self.min, self.max)
        else:
            return "No known type defined"
db.register([Diel])