import unittest
from larva_library import app
from mongokit import Connection

class FlaskMongoTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        self.db = Connection(app.config['MONGODB_HOST'], app.config['MONGODB_PORT'])[app.config['MONGODB_DATABASE']]
        with self.app.session_transaction() as sess:
            sess['user_email'] = u'testing@larvalibrary.com'

    def tearDown(self):
        self.db.drop_collection("capability")
        self.db.drop_collection("diel")
        self.db.drop_collection("taxis")
        self.db.drop_collection("lifestage")
        self.db.drop_collection("libraries")
        self.db.drop_collection("users")