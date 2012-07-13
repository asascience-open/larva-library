import os, sys

# set up path directory to read the larva_library module
INSTALL_PATH = os.path.abspath('.')
sys.path.append(INSTALL_PATH)

# set os environs
os.environ['APPLICATION_SETTINGS'] = 'development.py'
os.environ['SECRET_KEY'] = 'shhdonttellanyone'
os.environ['GOOGLE_CLIENT_SECRET'] = 'fakeituntilyoumakeit'
os.environ['GOOGLE_CLIENT_ID'] = 'fakeitifyoudontbelong'
os.environ['FACEBOOK_APP_ID'] = 'fakeitifyoureoutofdirection'
os.environ['FACEBOOK_APP_SECRET'] = 'icanfakeitall'

import larva_library
import unittest
import random
from flask import session

random.seed()

def random_string(number_of_chars=1):
    rdn_set = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',' ']
    result = ''
    for i in range(0,number_of_chars):
        result += rdn_set[random.randint(0,26)]
    return result

def random_keyword_string(number_of_kwrds=1):
    rdn_set = ['keyword1','keyword2','keyword3','keyword4','keyword5','doesexist','joker','crouton','fork','bottle','phone','book','pad','head','paper','pen','pencil']
    result = ''
    for i in range(0,number_of_kwrds):
        result += rdn_set[random.randint(0,16)] + ','
    return result.rstrip(',')

class LibraryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        larva_library.app.config['TESTING'] = True
        self.app = larva_library.app.test_client()
        self.app.post('/testing/set/email', data=dict(user_email='fake@email.com'))

    @classmethod
    def tearDownClass(self):
        # clear our working db
        #self.app.get('/library/remove_entries', follow_redirects=True)
        pass

    def test_index(self):
        # make sure we can talk to index
        rv = self.app.get('/')
        self.assertEqual(200, rv.status_code)

    def test_add_entries(self):
        # add an entry following all redirects
        # set false user_session
        # create x_entries
        x_entries = random.randint(20,30)
        genus_set = ['genusA','genusB','genusC','genusD']
        for i in range(0,x_entries):
            # setup our entries
            lib_name = 'name'+str(i)
            # get our genus
            genus = genus_set[random.randint(0,3)]
            # species
            species = 'species'+str(i % random.randint(19,20))
            # common name
            common_name = random_string(random.randint(10,20))
            #keywords
            keywords = random_keyword_string(random.randint(5,7))
            # create the entry with several calls
            rv = self.app.post('/library/wizard/page/1', data=dict(
                    lib_name=lib_name,
                    genus=genus,
                    species=species,
                    common_name=common_name,
                ), follow_redirects=True)
            rv = self.app.post('/library/wizard/page/2', data=dict(
                    keywords=keywords
                ), follow_redirects=True)
            rv = self.app.post('/library/wizard/page/3', data=dict(), follow_redirects=True)
            assert 'Successfully added entry' in rv.data

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

if __name__ == '__main__':
    unittest.main()
