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
    query['_status'] = unicode('public')
    if keywords is not None:
        query['_keywords'] = keywords

    return db.Library.find(query)

def retrieve_entries_for_user(user_id, keywords=None):
    query = dict()
    query['user'] = user_id
    if keywords is not None:
        query['_keywords'] = keywords

    return db.Library.find(query)

def retrieve_by_id(entry_ids, email=None):
    entry_list = list()

    if entry_ids is None:
        flash("Emtpy id set received")

    else:
        entry_ids = [x for x in entry_ids.split(',') if x]
        # create a query dict from the ids
        query = dict()
        tlist = list()

        for libid in entry_ids:
            tlist.append(dict(_id=ObjectId(libid.encode('ascii','ignore'))))

        query["$or"] = tlist
        results = db.Library.find(query)
        for entry in results:
            entry_list.append(entry)

    return entry_list

def retrieve_by_terms(terms, email=None, user_only=False):
    entry_list = list()

    if terms is None:
        # flash error and return empty result
        flash("Emtpy search params")

    else:
        # terms should be a comma deliminated string; remove any trailing commas
        terms = terms.rstrip(',')
        keywords = {'$all':terms.split(',')}

        if email is not None:
            search_result = retrieve_entries_for_user(email, keywords=keywords)
            for result in search_result:
                entry_list.append(result)

        if user_only is False:
            search_result = retrieve_public_entries(keywords)
            for result in search_result:
                if result not in entry_list:
                    entry_list.append(result)

    return entry_list

def retrieve_all(email=None, user_only=False):
    entry_list = list()

    # retrieve user and public entries; add each entry's json representation
    if email is not None:
        entries = retrieve_entries_for_user(email)
        for entry in entries:
            entry_list.append(entry)

    #get the master/public list and add it
    if user_only is False:
        entries = retrieve_public_entries()
        for entry in entries:
            if entry not in entry_list:
                entry_list.append(entry)

    return entry_list

def import_entry(entry, user):
    # assume entry is a dict
    if not isinstance(entry, dict):
        # not a dict, exit
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
