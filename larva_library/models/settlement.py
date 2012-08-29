from mongokit import Document
from larva_library import db

class Settlement(Document):
    __collection__ = 'settlements'
    use_dot_notation = True
    structure = {
        'upper'     : float,
        'lower'     : float,
        'type'      : unicode
    }
db.register([Settlement])