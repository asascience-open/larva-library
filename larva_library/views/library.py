from flask import url_for, request, redirect, flash, render_template, session, send_file, make_response, jsonify
from larva_library import app, db
from larva_library.models.library import LibrarySearch, Library, BaseWizard
from utils import retrieve_by_terms, retrieve_all, login_required, import_entry
from shapely.wkt import loads
from shapely.geometry import Point
from dateutil.parser import parse
import json
import datetime
import time
import pytz

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

@app.route('/library/<ObjectId:library_id>.json', methods=['GET'])
def json_view(library_id):
    entry = db.Library.find_one({'_id': library_id})
    return jsonify({"results" : [json.loads(entry.to_json())] })

@app.route("/library/search", methods=["POST", "GET"])
def library_search():

    if request.method == 'GET':
        return redirect(url_for('index'))

    form = LibrarySearch(request.form)

    if form.search_keywords.data is None or form.search_keywords.data == '':
        flash('Please enter a search term')
        return render_template('index.html', form=form)

    # Build query; first look for entries that belong to user, then look for entries that are marked public
    keywords = form.search_keywords.data
    entries = retrieve_by_terms(keywords, email=session.get('user_email', None), owned=form.user_owned.data)

    if len(entries) == 0:
        flash("Searching for '%s' returned 0 results" % keywords)
        return render_template('index.html', form=form)

    return render_template('library_list.html', libraries=entries)

@app.route("/library/search.json", methods=["GET"])
def library_json_search():
    email = request.args.get("email", None)
    keywords = request.args.get("terms", None)
    owned = bool(request.args.get("owned", False))

    results = retrieve_by_terms(keywords, email=email, owned=owned)
    entries = [json.loads(js.to_json()) for js in results]

    return jsonify({"results" : entries})

@app.route("/library/<ObjectId:library_id>.clone", methods=["GET"])
@login_required
def library_clone(library_id):

    entry = db.Library.find_one({'_id': library_id})
    entry_clone = entry.clone()
    # make sure name and user are unique pair
    entry_clone['user'] = unicode(session['user_email'])
    entry_clone.ensure_unique()
    entry_clone.build_keywords()
    db.libraries.reindex()
    entry_clone.save()

    return redirect(url_for('detail_view', library_id=entry_clone._id))

@app.route('/library/import', methods=['GET','POST'])
@login_required
def import_library():
    # using login decorator
    if request.method == 'POST':
        jsonfile_storage = request.files.get('jsonfile')
        stringStream = jsonfile_storage.stream
        stringStream.seek(0)
        entry_dict = json.loads(stringStream.getvalue().replace("\'", "\""))
        entry_list = entry_dict.values()[0] # assume the higher level dictionary only has one key

        if entry_list is None:
            flash("invalid file uploaded, please try again")
            return redirect(url_for('index'))

        # iterate through the entry list and add the entry; note: entries at this point are strings, we need to pass in dicts
        for entry in entry_list:
            # app.logger.info(json.dumps(entry))
            import_entry(json.dumps(entry), session['user_email'])

        # rebuild the indexes
        db.libraries.reindex()

        return redirect(url_for('index'))

    return render_template('library_import.html')

@app.route('/library')
def list_library():
    # retrieve entries marked as public and that belong to the user
    entry_list = list()
    user = session.get('user_email', None)

    entry_list = retrieve_all(user)

    if len(entry_list) == 0:
        flash('No entries exist in the library')

    return render_template('library_list.html', libraries=entry_list)


@app.route('/library/wizard', methods=['GET','POST'])
@login_required
def library_wizard():
    form = BaseWizard(request.form)

    if request.method == 'POST' and form.validate():

        # Setup the polygon
        geo_positional_data = None
        if request.form.get('geo') is not None:
            pts = []
            geo_string = request.form.get('geo')
            point_array = geo_string.split('),(')
            try:
                for pt in filter(None, point_array):
                    pt = pt.split(",")
                    pts.append((float(pt[1].replace(")","")),float(pt[0].replace("(",""))))
                # Create the polygon
                geo_positional_data = unicode(Polygon(pts).wkt)
            except:
                app.logger.warning("Could not build Polygon from: %s" % point_array)

        entry = db.Library()
        form.populate_obj(entry)

        lib = dict()
        lib['geometry'] = geo_positional_data
        lib['created'] = datetime.datetime.utcnow()
        lib['user'] = session['user_email'] # Safe because of @login_required decorator

        entry.copy_from_dictionary(lib)
        if entry.local_validate() is False:
            flash('%s already exists, please change the name to submit' % (entry.name))
        else:
            entry.build_keywords()
            db.libraries.ensure_index('_keywords')
            entry.save()

            # rebuild the indexes
            db.libraries.reindex()
                
            flash('Created library entry %s' % str(entry._id))
            return redirect(url_for('detail_view', library_id=entry._id ))

    return render_template('library_wizard.html', form=form)


@app.route('/library/<ObjectId:library_id>/edit', methods=['GET','POST'])
@login_required
def library_edit_wizard(library_id):

    # Get library object
    entry = db.Library.find_one({'_id':library_id})
    if entry is None:
        flash('Cannot find ' + str(library_id) + ' for editing')
        return redirect(url_for('index'))

    # Permissions
    if session.get('user_email', None) != entry.user:
        flash('%s does not have permission to edit this entry')
        return redirect(url_for('index'))

    form = BaseWizard(request.form, obj=entry)
    
    if request.method == 'POST' and form.validate():

        form.populate_obj(entry)

        # Setup the polygon
        geo_positional_data = None
        if request.form.get('geo') is not None:
            pts = []
            geo_string = request.form.get('geo')
            point_array = geo_string.split('),(')
            try:
                for pt in filter(None, point_array):
                    pt = pt.split(",")
                    pts.append((float(pt[1].replace(")","")),float(pt[0].replace("(",""))))
                # Create the polygon
                geo_positional_data = unicode(Polygon(pts).wkt)
            except:
                app.logger.warning("Could not build Polygon from: %s" % point_array)

        lib = dict()
        lib['geometry'] = geo_positional_data
        lib['created'] = datetime.datetime.utcnow()
        lib['user'] = session['user_email'] # Safe because of @login_required decorator

        entry.copy_from_dictionary(lib)
        entry.build_keywords()
        db.libraries.ensure_index('_keywords')
        entry.save()

        # rebuild the indexes
        db.libraries.reindex()
            
        flash('Edited library entry %s' % str(entry._id))
        return redirect(url_for('detail_view', library_id=entry._id ))
    else:
        marker_positions = []
        # load the polygon
        if entry.geometry:
            polygon = loads(entry.geometry)
            for pt in polygon.exterior.coords:
                # Google maps is y,x not x,y
                marker_positions.append((pt[1], pt[0]))
        form.markers = marker_positions

    return render_template('library_wizard.html', form=form)


#debug
@app.route('/library/remove_entries')
def remove_libraries():
    db.drop_collection('libraries')
    return redirect(url_for('index'))
