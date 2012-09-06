from mongokit import Document
from larva_library import db
from mongokit import OR

class Capability(Document):
    __collection__ = 'capability'
    use_dot_notation = True
    structure = {
        'vss'               : OR(int, float),
        'variance'          : OR(int, float),
        'swim_turning'      : unicode,
        'nonswim_turning'   : unicode
    }
db.register([Capability])