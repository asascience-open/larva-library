from mongokit import Document
from larva_library import db
from mongokit import OR

class Settlement(Document):
    __collection__ = 'settlements'
    use_dot_notation = True
    structure = {
        'upper'     : OR(int, float),
        'lower'     : OR(int, float),
        'type'      : unicode
    }
db.register([Settlement])