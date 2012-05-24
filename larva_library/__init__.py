from flask import Flask
from flask.ext.mongokit import MongoKit
from oauth import OAuth
from os import environ
#import logging
#from logging import FileHandler

# Create application object
app = Flask(__name__)
app.config.from_object('larva_library.default')
app.config.from_envvar('APPLICATION_SETTINGS', silent=True)

#sets up a file for logging, because sometimes stdout just won't work
#app.logger.addHandler(file_handler)
#file_handler = FileHandler('log.txt')
#file_handler.setLevel(logging.INFO)

oauth = OAuth()
if app.config.get('DEBUG') == True:
    fb_key = environ.get('FACEBOOK_LOCAL_APP_ID')
    fb_secret = environ.get('FACEBOOK_LOCAL_APP_SECRET')
else:
    fb_secret = environ.get('FACEBOOK_APP_SECRET')
    fb_key = environ.get('FACEBOOK_APP_ID')

app.config['SECRET_KEY'] = environ.get('SECRET_KEY')

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=fb_key,
    consumer_secret=fb_secret,
    request_token_params={'scope': 'email'}
)
google = oauth.remote_app('google',
    base_url=None,
    request_token_url=None, #this should only exist for OAuth1.0
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    consumer_key=environ.get('GOOGLE_CLIENT_ID'),
    consumer_secret=environ.get('GOOGLE_CLIENT_SECRET'),
    access_token_method='POST',
    request_token_params={'response_type':'code','scope':'https://www.googleapis.com/auth/userinfo.email','grant_type':'authorization_code'}
)

# Create the database connection
db = MongoKit(app)

# Import everything
import larva_library.views
import larva_library.models
