from flask import url_for, request, redirect, flash, render_template, session, send_file
from larva_library import app, db
from larva_library.models.library import LibrarySearch, Library
from utils import retrieve_public_entries, retrieve_entries_for_user, retrieve_by_id, retrieve_by_terms, retrieve_all
from shapely.wkt import loads
from shapely.geometry import Point
from bson import ObjectId
import StringIO

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

@app.route("/library/search", methods=["POST"])
def library_search():
    form = LibrarySearch(request.form)

    if form.search_keywords.data is None or form.search_keywords.data == '':
        flash('Please enter a search term')
        return redirect(url_for('index'))

    # Build query; first look for entries that belong to user, then look for entries that are marked public
    _keystr = form.search_keywords.data.rstrip(',')
    keywords = {'$all':_keystr.split(',')}
    entries = list()
    if session.get('user_email') is not None:
        search = retrieve_entries_for_user(session.get('user_email'), keywords=keywords)
        for entry in search:
            entries.append(entry)

    if form.user_owned is not True:
        search = retrieve_public_entries(keywords=keywords)
        for entry in search:
            if entry not in entries:
                entries.append(entry)

    if len(entries) == 0:
        flash("Could not find any entries with the specified search criteria")

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

    if len(entry_list) == 0:
        flash('No entries copied from user')

    entries = retrieve_public_entries()
    count = entries.count()
    for entry in entries:
        if entry not in entry_list:
            entry_list.append(entry)

    if len(entry_list) == 0:
        flash('No entries exist in the library')

    return render_template('library_list.html', libraries=entry_list)

#debug
@app.route('/library/remove_entries')
def remove_libraries():
    db.drop_collection('libraries')
    return redirect(url_for('index'))

#temp
@app.route('/library/<ObjectId:library_id>/edit')
def edit_entry(library_id):
    if library_id is None:
        flash('Cannot edit empty entry, try making a new one instead')
        return redirect(url_for('index'))

    entry = db.Library.find_one({'User':session.get('user_email', None), '_id':library_id})
    if entry is None:
        flash('Cannot find ' + str(library_id) + ' for current user, please make sure you have privileges necessary to edit the entry')
        return redirect(url_for('index'))

    #Pass along entry as form
    return redirect(url_for('wizard_page_one', form=entry))

@app.route('/library.json', methods=['GET'])
def larva_json_service():
    # overhaul: query vars to look for library_ids, terms, email, user_owned_only
    json_result = dict()
    library_list = list()
    entry_json_list = list()

    id_list = request.args.get("library_ids")
    email = request.args.get("email")
    terms = request.args.get("terms")
    user_only = request.args.get("user_owned_only", default=False)

    if id_list is not None:
        library_list = retrieve_by_id(id_list, email)

    elif terms is not None:
        library_list = retrieve_by_terms(terms, email, user_only)

    else:
        library_list = retrieve_all(email)

    if len(library_list) == 0:
        flash("Unable to find any entries matching criterion, please try again")
        return redirect(url_for('index.html'))

    # collect all of the json entries into one list
    for entry in library_list:
       entry_json_list.append(entry.to_json())

    json_result['library_results'] = entry_json_list

    #create a string stream to act as a temporary file for downloading the json
    stringStream = StringIO.StringIO()
    stringStream.write(json_result)
    # ensure that the stream starts at the beginning for the read to file
    stringStream.seek(0)

    return send_file(stringStream, attachment_filename="library_search.json", as_attachment=True)
