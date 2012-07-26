from functools import wraps
from flask import request, redirect, url_for, session, flash
from larva_library import db
from bson import ObjectId
import datetime

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

def import_entry(entry, user):
    # assume entry is a dict
    if not isinstance(entry, dict):
        # not a dict, exit
        flash('entry received was not a dictionary')
        return

    # clean up before inserting; remove generated keys, change user, _status and created to reflect new ownership
    if '_id' in entry:
        del entry['_id']

    if '_keywords' in entry:
        del entry['_keywords']

    entry['user'] = unicode(user)
    entry['_status'] = unicode('private')
    entry['created'] = datetime.datetime.utcnow()

    # need to pull out the life stages and re-add them as well
    lifestages = list()
    if 'lifestages' in entry:
        lifestages = entry['lifestages']
        del entry['lifestages']

    lib_entry = db.Library()
    lib_entry.copy_from_dictionary(entry)
    lib_entry.build_keywords()

    # validate that the entry isn't already in the db
    name = lib_entry['name']
    name_id = 0
    while lib_entry.validate() is False:
        name_id += 1
        lib_entry['name'] = unicode(str(name) + str(name_id))

    db.libraries.ensure_index('_keywords')

    # import each of the lifestages and append them to the entry
    for lifestage in lifestages:
        import_lifestage(lifestage, lib_entry)

    # save the entry
    lib_entry.save()

    return

def import_lifestage(lifestage, entry):
    # make sure both are not none:
    if lifestage is None or entry is None or not isinstance(lifestage, dict):
        return

    # clean up the lifestage:
    if '_id' in lifestage:
        del lifestage['_id']

    # create the lifestage in the database, then append it to the entry
    lib_lifestage = db.LifeStage()
    lib_lifestage.copy_from_dictionary(lifestage)
    # save and append
    lib_lifestage.save()
    entry.lifestages.append(lib_lifestage)

    return
