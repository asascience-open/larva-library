from flask import Flask
from mongokit import Connection, Database
from flaskext.oauth import OAuth

# Create application object
app = Flask(__name__)
app.config.from_object('larva_library.default')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

oauth = OAuth()
facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=app.config.get('FACEBOOK_APP_ID'),
    consumer_secret=app.config.get('FACEBOOK_APP_SECRET'),
    request_token_params={'scope': 'email'}
)
twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=app.config.get('TWITTER_CONSUMER_KEY'),
    consumer_secret=app.config.get('TWITTER_CONSUMER_SECRET')
)
google = oauth.remote_app('google',
    base_url='https://accounts.google.com/',
    request_token_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://www.googleapis.com/oauth2/v1/tokeninfo',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    consumer_key=app.config.get('GOOGLE_CLIENT_ID'),
    consumer_secret=app.config.get('GOOGLE_CLIENT_SECRET')
)

# Create connection to Mongo
connection = Connection(host=app.config.get('MONGODB_HOST'),
            			port=app.config.get('MONGODB_PORT'))

# Create the database connection
db = Database(connection, app.config.get('MONGODB_DATABASE'))
if app.config.get('MONGODB_USERNAME'):
	db.authenticate(
		app.config['MONGODB_USERNAME'],
		app.config['MONGODB_PASSWORD']		
	)

# Import everything
import larva_library.views
import larva_library.models
