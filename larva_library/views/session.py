from flask import Module, request, url_for, render_template, redirect, session, flash
from larva_library import db, app, facebook, google
from json import loads
from werkzeug import url_encode
from httplib2 import Http
from flask.wrappers import Request
from larva_library.models.user import User, find_or_create_by_email

@app.route('/logout')
def logout():
    session.pop('facebook_token', None)
    session.pop('google_token', None)
    session.pop('user_id', None)
    session.pop('user_email', None)

    flash('Signed out')
    return redirect(request.referrer or url_for('index'))

# FACEBOOK
@app.route('/login_facebook')
def login_facebook():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))

@app.route('/login/facebook_authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        flash (u'Access denied.')
        return redirect(url_for('index'))
    
    next_url = request.args.get('next') or url_for('index')
    session['facebook_token'] = (resp['access_token'], '')
    #request 'me' to get user id and email
    me = facebook.get('/me')

    user = find_or_create_by_email(me.data['email'])
    set_user_session(user)

    flash('Signed in as ' + session['user_email'])
    return redirect(next_url)

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('facebook_token')

#GOOGLE
@app.route('/login_google')
def login_google():
    # for some reason url_for('google_authorized') is only returning '/google_auth' instead of the actual url like the other use cases
    # hardcoding the url for now http://larva-library.herokuapp.com/google_auth
    return google.authorize(callback=url_for('google_authorized',
        _external=True))
    
@app.route('/login/google_authorized')
@google.authorized_handler
def google_authorized(resp):
    if resp is None:
        flash(u'Access denied.')
        return redirect(url_for('index'))
    session['google_token'] = resp['access_token']
    # create request for email
    body = {'access_token': session.get('google_token')}
    req = Http(".cache")
    # request email
    resp, content = req.request('https://www.googleapis.com/oauth2/v1/userinfo?' + url_encode(body))
    # parse JSON into dict
    content = loads(content)
    # Set session variables
    user = find_or_create_by_email(content.get('email'))
    set_user_session(user)

    flash('Signed in as ' + session.get('user_email'))
    return redirect(url_for('index'))

def set_user_session(user):
    session['user_email'] = user.email
