from mongokit import Document
from larva_library import db

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