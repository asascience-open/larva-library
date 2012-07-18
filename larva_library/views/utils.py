from functools import wraps
from flask import request, redirect, url_for, session, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            session['user_email']
        except KeyError:
            flash('Must be logged in to proceed')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function