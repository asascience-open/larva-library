from flask import Flask
from flask.ext.mongokit import MongoKit
from oauth import OAuth
import os

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
google = oauth.remote_app('google',
    base_url=None,
    request_token_url=None, #this should only exist for OAuth1.0
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    consumer_key=app.config.get('GOOGLE_CLIENT_ID'),
    consumer_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
    access_token_method='POST',
    request_token_params={'response_type':'code','scope':'https://www.googleapis.com/auth/userinfo.email','grant_type':'authorization_code'}
)

# Create the database connection
db = MongoKit(app)

# Logging if STDOUT is not working
if app.config.get('LOG_FILE') == True:
    import logging
    from logging import FileHandler
    file_handler = FileHandler('log.txt')
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

# Import everything
import larva_library.views
import larva_library.models
