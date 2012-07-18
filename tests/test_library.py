from larva_library import app
import unittest

class LibraryTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        with self.app.session_transaction() as sess:
            sess['user_email'] = u'testing@larvalibrary.com'

    def tearDown(self):
        # clear our working db
        #self.app.get('/library/remove_entries', follow_redirects=True)
        pass

    def test_index(self):
        # make sure we can talk to index
        rv = self.app.get('/')
        self.assertEqual(200, rv.status_code)

    def test_retrieve_db(self):
        # lets see if we can talk to the database
        rv = self.app.get('/library')
        self.failIf('No entries exist in the library' in rv.data)

    def test_search_db(self):
        # try various searches
        rv = self.app.post('/library/search', data=dict(
                search_keywords='doesnotexist'
            ), follow_redirects=True)
        # check out our data to see if we did not find anything, we is expected
        assert 'Search returned 0 results' in rv.data

        rv = self.app.post('/library/search', data=dict(
                search_keywords='keyword1,doesexist'
            ), follow_redirects=True)
        # should get something in data if it does exist
        self.failIf('Search returned 0 results' in rv.data)
