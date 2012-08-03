from flask.ext.mongokit import Document
from larva_library import app, db
from larva_library.models.library import Library

class User(Document):
    __collection__ = 'users'
    required_fields = ['email']
    indexes = [{'fields' : 'email', 'unique' : True}]
    use_dot_notation = True
    structure = {
        'name': unicode,
        'email': unicode,
        'institution': unicode,
        'admin': bool
    }

    def __repr__(self):
        return '<User %r>' % (self.email)

db.register([User])

def find_or_create_by_email(email):
    u = db.User.find_one({'email':email})
    if u is None:
        u = db.User()
        u['email'] = unicode(email)
        u.save()

    return u
