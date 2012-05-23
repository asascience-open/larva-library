from flask import Module, request, url_for, render_template, redirect, session, flash
from larva_library import db, app, facebook, twitter, google

@app.route('/logout')
def logout():
    session.pop('twitter_secret', None)
    session.pop('twitter_token', None)
    session.pop('facebook_token', None)
    session.pop('user_id', None)
    flash('Signed out')
    return redirect(request.referrer or url_for('show_reports'))

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
        return redirect(url_for('show_reports'))

    next_url = request.args.get('next') or url_for('show_reports')
    session['facebook_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    session['user_id'] = me.data['email']
    flash('Signed in as ' + session['user_id'])
    return redirect(next_url)

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('facebook_token')

# TWITTER
@app.route('/login_twitter')
def login_twitter():
    return twitter.authorize(callback=url_for('twitter_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/login/twitter_authorized')
@twitter.authorized_handler
def twitter_authorized(resp):
    if resp is None:
        flash(u'Access denied.')
        return redirect(url_for('show_reports'))

    next_url = request.args.get('next') or url_for('show_reports')
    session['twitter_token'] = resp['oauth_token']
    session['twitter_secret'] = resp['oauth_token_secret']
    session['user_id'] = resp['screen_name']
    flash('Signed in as ' + session['user_id'])
    return redirect(next_url)

#GOOGLE
@app.route('/login_google')
def login_google():
    return google.authorize(callback=url_for('google_authorized',
        next=request.referrer or None))
    
@app.route('/google_auth')
@google.authorized_handler
def google_authorized(resp):
    if resp is None:
        flash(u'Access denied.')
        return redirect(url_for('show_reports'))
    
    next_url = request.args.get('next') or url_for('show_reports')
    print resp
    print dir(resp)
    print vars(resp)
    return redirect(next_url)

@twitter.tokengetter
def get_twitter_token():
    if session.get('twitter_token') and session.get('twitter_secret'):
        return session.get('twitter_token'), session.get('twitter_secret')
    else:
        return None
