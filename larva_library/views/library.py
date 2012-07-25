from flask import url_for, request, redirect, flash, render_template, session, send_file
from larva_library import app, db
from larva_library.models.library import LibrarySearch, Library
from utils import retrieve_by_id, retrieve_by_terms, retrieve_all, import_entry, login_required
from shapely.wkt import loads
from shapely.geometry import Point
from ast import literal_eval
import StringIO
import json

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
    keywords = form.search_keywords.data
    entries = list()
    if session.get('user_email') is not None:
        entries = retrieve_by_terms(keywords, email=session.get('user_email'), user_only=form.user_owned.data)
    else:
        entries = retrieve_by_terms(keywords, user_only=form.user_owned.data)

    if len(entries) == 0:
        flash("Could not find any entries with the specified search criteria")
        return redirect(url_for('index'))

    return render_template('library_list.html', libraries=entries, filename="search_result_"+keywords.replace(',',''))

@app.route('/library')
def list_library():
    # retrieve entries marked as public and that belong to the user
    entry_list = list()
    user = session.get('user_email', None)

    entry_list = retrieve_all(user)

    if len(entry_list) == 0:
        flash('No entries exist in the library')

    return render_template('library_list.html', libraries=entry_list, filename="library_list")

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

@app.route('/library/import', methods=['GET','POST'])
@login_required
def import_library():
    # using login decorator
    if request.method == 'POST':
        jsonfile_storage = request.files.get('jsonfile')
        stringStream = jsonfile_storage.stream
        stringStream.seek(0)
        entry_dict = literal_eval(stringStream.getvalue())
        entry_list = entry_dict.get('library_results')

        if entry_list is None:
            flash("invalid file uploaded, please try again")
            return redirect(url_for('index'))

        # iterate through the entry list and add the entry; note: entries at this point are strings, we need to pass in dicts
        for entry in entry_list:
            import_entry(json.loads(entry), session['user_email'])

        # rebuild the indexes
        db.libraries.reindex()

        return redirect(url_for('index'))

    return render_template('library_import.html')


@app.route('/library.json', methods=['GET'])
def json_service():
    # overhaul: query vars to look for library_ids, terms, email, user_owned_only
    json_result = dict()
    library_list = list()
    entry_json_list = list()

    id_list = request.args.get("library_ids")
    email = request.args.get("email")
    terms = request.args.get("terms")
    user_only = request.args.get("user_owned_only", default=False)
    file_name = request.args.get("filename")

    if file_name is None:
        file_name = "library_search"

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

    file_name += ".json"

    return send_file(stringStream, attachment_filename=file_name, as_attachment=True)
