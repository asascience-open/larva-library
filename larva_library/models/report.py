from mongokit import Document
from larva_library import db, app, connection
from pymongo import GEO2D

class Report(Document):
    structure = {
        'loc': list,
        'winds': unicode,
        'waves': unicode,
        'currents': unicode,
        'comments': unicode,
        'user_id': unicode
    }
    #validators = {
    #    'name': max_length(50),
    #    'email': max_length(120)
    #}
    use_dot_notation = True
    def __repr__(self):
        return '<Report %r>' % (self.id)

connection.register([Report])
# Geo index on Report
db.reports.ensure_index([("loc", GEO2D)])