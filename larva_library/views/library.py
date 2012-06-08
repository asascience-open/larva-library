from flask import url_for, request, redirect, flash, render_template, session
from larva_library import app, db
from larva_library.models.library import LibrarySearch
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

    # return the positional data into usable points for markers on google maps
    marker_poisitions = []
    # load the point data and put the positions into tuples
    if entry.Geometry:
        for pos in entry.Geometry:
            #flash(pos)
            point = loads(pos)
            position_tuple = (point.x,point.y)
            marker_poisitions.append(position_tuple)

    entry['Markers'] = marker_poisitions

    return render_template('library_detail.html', entry=entry)

@app.route("/library/search", methods=["POST"])
def library_search():
    form = LibrarySearch(request.form)

    if form.search_keywords.data is None or form.search_keywords.data == '':
    	flash('Please enter a search term')
    	return redirect(url_for('index'))

    # Build query
    query = dict()
    _keyword_query = dict()
    _keystr = form.search_keywords.data.rstrip(',')
    query['_keywords'] = {'$all':_keystr.split(',')}
    if form.user_owned.data == True and session.get('user_email') is not None:
    		query['User'] = session.get('user_email')

    libraries = db.Library.find(query)
    if libraries.count() == 0:
        flash('Search returned 0 results')
        return redirect(url_for('index'))

    return render_template('library_list.html', libraries=libraries)

@app.route('/library')
def list_library():
    # retrieve entire db and pass it to the html
    libraries = db.Library.find()
    if libraries.count() == 0:
        flash('No entries exist in the library')
    return render_template('library_list.html', libraries=libraries)

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