from functools import wraps
from flask import request, redirect, url_for, session, flash
from larva_library import db, app
import datetime
import json
from larva_library.models.library import Library

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

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            assert len(list(db.User.find({'admin': True, 'email': session['user_email']}))) > 0
        except KeyError:
            flash('Must be logged in to proceed')
            return redirect(url_for('index'))
        except AssertionError:
            flash('Must be logged in as an adminstrator to proceed')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def str_to_num(string):
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except:
            return string

def authorize_entry_write(entry=None, user=None):
    if entry is None:
        return False

    if user is not None:
        if entry.user == user.email or user.admin:
            return True
            
    return False

def authorize_entry(entry=None, user=None):
    if entry is None:
        return False
    if entry.status == Library.STATUS_PUBLIC or entry.status == Library.STATUS_DEPREC:
        return True
    if user is not None:
        if entry.user == user.email or user.admin:
            return True
    return False

def authorize_owned(entry=None, user=None):
    if entry is None:
        return False
    if user is not None:
        if entry.user == user.email:
            return True
    return False

def authorize_list(entries=None, user=None):
    if entries is None:
        entries = []

    return (entry for entry in entries if authorize_entry(entry=entry,user=user))

def retrieve_all(user=None, only_owned=None):
    if only_owned is None:
        only_owned = False
    matches = db.Library.find()
    matches = authorize_list(entries=matches, user=user)
    if only_owned is True:
        return (match for match in matches if authorize_owned(entry=match,user=user))
    return matches

def retrieve_by_terms(terms, user=None, only_owned=None):
    if only_owned is None:
        only_owned = False
    if terms is None:
        return []
    # terms should be a comma deliminated string; remove any trailing commas
    # and split into an array
    keywords = { '$all' : terms.rstrip(',').split(',') }
    matches = db.Library.find({ '_keywords' : keywords })
    matches = authorize_list(matches, user)
    if only_owned is True:
        return (match for match in matches if authorize_owned(entry=match,user=user))
    return matches
