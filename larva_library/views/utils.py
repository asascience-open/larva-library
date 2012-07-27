from functools import wraps
from flask import request, redirect, url_for, session, flash
from larva_library import db, app
from larva_library.models.library import remove_id
import datetime
import json

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

def str_to_num(string):
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except:
            return string

def retrieve_public_entries(keywords=None):
    query = dict()
    query['status'] = unicode('public')
    if keywords is not None:
        query['_keywords'] = keywords

    return db.Library.find(query)

def retrieve_entries_for_user(email, keywords=None):
    query = dict()
    query['user'] = email
    if keywords is not None:
        query['_keywords'] = keywords

    return db.Library.find(query)

def retrieve_by_terms(terms, email=None, owned=False):
    entry_list = []

    if terms is None:
        return entry_list

    # terms should be a comma deliminated string; remove any trailing commas
    # and split into an array
    keywords = { '$all' : terms.rstrip(',').split(',') }

    if email is not None:
        email_result = retrieve_entries_for_user(email, keywords=keywords)
        for result in email_result:
            entry_list.append(result)

    if owned is False:
        public_result = retrieve_public_entries(keywords=keywords)
        for result in public_result:
            if result not in entry_list:
                entry_list.append(result)

    return entry_list

def retrieve_all(email=None, owned=False):
    entry_list = list()

    # retrieve user and public entries; add each entry's json representation
    if email is not None:
        entries = retrieve_entries_for_user(email)
        for entry in entries:
            entry_list.append(entry)

    #get the master/public list and add it
    if owned is False:
        entries = retrieve_public_entries()
        for entry in entries:
            if entry not in entry_list:
                entry_list.append(entry)

    return entry_list

def copy_value(key, item=None):
    if isinstance(item, list) and len(item):
        n_list = [ copy_value(key, sub) for sub in item ]
        return n_list
    elif isinstance(item, dict):
        # check for a recognized key
        doc = dict()
        # app.logger.info("key is %s" % key)
        if key == "library":
            doc = db.Library()
        elif str(key) == "lifestages":
            doc = db.LifeStage()
        elif str(key) == "diel":
            doc = db.Diel()
        elif str(key) == "taxis":
            doc = db.Taxis()
        for skey in item.keys():
            doc[skey] = copy_value(skey, item[skey])

        return doc

    return item

def import_entry(entry, user):
    entry_dict = json.loads(entry)

    n_lib = copy_value("library", entry_dict)

    # remove ids
    remove_id(n_lib)
    n_lib['user'] = user
    n_lib['created'] = datetime.datetime.utcnow()
    # make sure we have a unique user/name pait
    n_lib.build_keywords()
    n_lib.ensure_unique()
    # rebuild keywords again to make sure they are correct
    n_lib.build_keywords()
    db.libraries.ensure_index('_keywords')
    n_lib.save()

    return
