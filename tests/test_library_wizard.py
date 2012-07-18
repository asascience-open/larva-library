from larva_library import app
import unittest
import random

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

class LibraryWizardTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        with self.app.session_transaction() as sess:
            sess['user_email'] = u'testing@larvalibrary.com'

    def tearDown(self):
        # clear our working db
        #self.app.get('/library/remove_entries', follow_redirects=True)
        pass

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
            geo_keywords = random_keyword_string(random.randint(5,7))

            geo = "(51.8279954420803, -150.12374999999997),(37.150279946816994, -142.74093749999997),(53.32335189700258, -136.41281249999997),(53.7412635745501, -143.79562499999997),(51.8279954420803, -150.12374999999997)"

            # create the entry with several calls
            rv = self.app.post('/library/wizard', data=dict(
                    name=lib_name,
                    genus=genus,
                    species=species,
                    common_name=common_name,
                    keywords=keywords,
                    geo_keywords=geo_keywords,
                    geo=geo,
                ), follow_redirects=True)

            assert 'Created library entry' in rv.data