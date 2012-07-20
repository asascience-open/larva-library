from flask import url_for, request, redirect, flash, render_template, session
from larva_library import app, db
from larva_library.models.library import LibrarySearch, Library
from shapely.wkt import loads
from shapely.geometry import Point
from bson import ObjectId

@app.route('/library/<ObjectId:library_id>', methods=['GET'])
def detail_view(library_id):
    if library_id is None:
        flash('Recieved an entry without an id')
        return redirect(url_for('index'))

    entry = db.Library.find_one({'_id': library_id})

    if entry is None:
        flash('Cannot find object ' + str(library_id))
        return redirect(url_for('index'))

    marker_positions = []
    # load the polygon
    if entry.geometry:
        polygon = loads(entry.geometry)
        for pt in polygon.exterior.coords:
            # Google maps is y,x not x,y
            marker_positions.append((pt[1], pt[0]))

    entry['markers'] = marker_positions

    return render_template('library_detail.html', entry=entry)

@app.route("/library/<ObjectId:library_id>/json", methods=['GET'])
def print_json(library_id):
    if library_id is None:
        flash('Recieved an entry without an id')
        return redirect(url_for('index'))

    entry = db.Library.find_one({'_id': library_id})

    if entry is None:
        flash('Cannot find object ' + str(library_id))
        return redirect(url_for('index'))

    json = entry.to_json();

    return render_template('print_json_rep.html', json=json)

@app.route("/library/search", methods=["POST"])
def library_search():
    form = LibrarySearch(request.form)

    if form.search_keywords.data is None or form.search_keywords.data == '':
        flash('Please enter a search term')
        return redirect(url_for('index'))

    # Build query; first look for entries that belong to user, then look for entries that are marked public
    _keystr = form.search_keywords.data.rstrip(',')
    query['_keywords'] = {'$all':_keystr.split(',')}
    if form.user_owned.data == True and session.get('user_email') is not None:
        query['user'] = session.get('user_email')

    search = retrieve_public_entries(keywords=keywords)
    for entry in search:
        if entry not in entries:
            entries.append(entry)

    return render_template('library_list.html', libraries=entries)

@app.route('/library')
def list_library():
    # retrieve entries marked as public and that belong to the user
    entry_list = list()
    user = session.get('user_email', None)
    if user is not None:
        entries = retrieve_entries_for_user(user)
        for entry in entries:
            entry_list.append(entry)

    entries = retrieve_public_entries()
    for entry in entries:
        if entry not in entry_list:
            entry_list.append(entry)

    if len(entry_list) == 0:
        flash('No entries exist in the library')

    return render_template('library_list.html', libraries=entry_list)

@app.route('/library/json')
def list_library_as_json():
    json = dict()
    entry_list = list()
    library_ids = request.args.get('library_ids', None)
    if library_ids is None:
        # retrieve user and public entries; add each entry's json representation
        user = session.get('user_email', None)
        if user is not None:
            entries = retrieve_entries_for_user(user)
            for entry in entries:
                entry_list.append(entry)

        #get the master/public list and add it
        entries = retrieve_public_entries()
        for entry in entries:
            if entry not in entry_list:
                entry_list.append(entry)

        if len(entry_list) == 0:
            flash('could not find any entries to download')
            return redirect(url_for('index'))
        
    else:
        library_ids = [x for x in library_ids.split(',') if x]
        # create a query dict from the ids
        query = dict()
        tlist = list()

        for libid in library_ids:
            tlist.append(dict(_id=ObjectId(libid.encode('ascii','ignore'))))

        query["$or"] = tlist
        results = db.Library.find(query)
        for entry in results:
            entry_list.append(entry)

    library_list = list()
    for entry in entry_list:
       library_list.append(entry.to_json())

    json['library'] = library_list

    return render_template('print_json_rep.html', json=json)

#debug
@app.route('/library/remove_entries')
def remove_libraries():
    db.drop_collection('libraries')
    return redirect(url_for('index'))
