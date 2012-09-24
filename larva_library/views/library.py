from flask import url_for, request, redirect, flash, render_template, session, send_file, make_response, jsonify
from larva_library import app, db
from larva_library.models.library import LibrarySearch, Library, BaseWizard
from larva_library.utils import remove_mongo_keys
from bson.objectid import ObjectId
from larva_library.views.helpers import login_required, retrieve_by_terms, retrieve_all, authorize_entry_write
from shapely.wkt import loads
from shapely.geometry import Point, Polygon
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
    user = db.User.find_one({ 'email' : session.get("user_email")})

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

    auth = False
        # Permissions
    if authorize_entry_write(entry=entry, user=user):
        auth = True

    return render_template('library_detail.html', entry=entry, auth=auth)

@app.route('/library/<ObjectId:library_id>.json', methods=['GET'])
def json_view(library_id):
    entry = db.Library.find_one({'_id': library_id})
    if entry is not None:
        jsond = json.loads(entry.to_json())
        remove_mongo_keys(jsond) #destructive method
        return jsonify({"results" : [jsond] })
    else:
        return jsonify({"results" : "No library entry with ID %s" % str(library_id) })

@app.route("/library/search", methods=["POST", "GET"])
def library_search():

    if request.method == 'GET':
        return redirect(url_for('index'))

    form = LibrarySearch(request.form)

    email = session.get('user_email', None)
    user = db.User.find_one({ 'email' : email })

    libraries = []
    if user is not None:
        libraries = retrieve_all(user=user, only_owned=True)

    if form.search_keywords.data is None or form.search_keywords.data == '':
        flash('Please enter a search term')
        return render_template('index.html', form=form, libraries=libraries)

    # Build query; first look for entries that belong to user, then look for entries that are marked public
    keywords = form.search_keywords.data

    entries = list(retrieve_by_terms(keywords, user=user, only_owned=form.user_owned.data))

    if len(entries) < 1:
        flash("Searching for '%s' returned 0 results" % keywords)
        return render_template('index.html', form=form, libraries=libraries)
    else:
        return render_template('library_list.html', libraries=entries)    

@app.route("/library/search.json", methods=["GET"])
def library_json_search():
    email = request.args.get("email", None)
    keywords = request.args.get("terms", None)
    only_owned = bool(request.args.get("owned", False))

    user = db.User.find_one({ 'email' : email })

    results = retrieve_by_terms(keywords, user=user, only_owned=only_owned)

    entries = [entry.simplified_json() for entry in results]

    return jsonify({"results" : entries})


@app.route('/library/import', methods=['POST'])
@app.route('/library/import.<string:format>', methods=['POST'])
def import_library(format=None):
    if format is None:
        format = 'html'

    if format != 'html' and format != 'json':
        raise ValueError("Only html and json formats are supported")

    email = None
    try:
        email = session['user_email']
    except:
        try:
            email = request.args['email']
        except:
            if format == 'html':
                flash("Must be logged in to import library entries")
                return redirect(url_for('index'))
            elif format == 'json':
                return jsonify( { 'results' : 'Must add an email parameter to request' } )

    if request.method == 'POST':

        entry_dict = None

        jsonfile_storage = request.files.get('jsonfile', None)
        json_data = request.form.get("config", None)

        try:
            # Are they POSTing a file?
            if jsonfile_storage is not None:
                stringStream = jsonfile_storage.stream
                stringStream.seek(0)
                entry_dict = json.loads(stringStream.getvalue())
            
            # Are they POSTing JSON?
            if json_data is not None:
                entry_dict = json.loads(json_data)

            entry_list = entry_dict.get('results', None) # assume the higher level dictionary only has one key
            assert entry_list is not None
            assert isinstance(entry_list, list)
        except:
            message = "Must upload a valid library file, please try again"
            if format == 'html':
                flash(message)
                return redirect(url_for('index'))
            elif format == 'json':
                return jsonify( { 'results' : message } )

        saved_items = []

        #app.logger.info(entry_list)

        for entry in entry_list:

            js = json.loads(json.dumps(entry))
            lifestages = []

            for lifestage in js.get('lifestages', []):

                diels = []
                taxis = []
                capability = None
                settlement = None

                for diel in lifestage.get('diel', []):
                    d = db.Diel.from_json(json.dumps(diel))
                    d.save()
                    diels.append(d)
                lifestage['diel'] = []

                for tx in lifestage.get('taxis', []):
                    t = db.Taxis.from_json(json.dumps(tx))
                    t.save()
                    taxis.append(t)
                lifestage['taxis'] = []

                c = lifestage.get('capability', None)
                if c is not None:
                    capability = db.Capability.from_json(json.dumps(c))
                    capability.save()
                    lifestage['capability'] = None

                s = lifestage.get('settlement', None)
                if s is not None:
                    settlement = db.Settlement.from_json(json.dumps(s))
                    settlement.save()
                    lifestage['settlement'] = None

                ls = db.LifeStage.from_json(json.dumps(lifestage))
                ls.diel = diels
                ls.taxis = taxis
                ls.capability = capability
                ls.settlement = settlement
                ls.save()
                lifestages.append(ls)

            js['lifestages'] = []
            js['user'] = email
            js['_keywords'] = []
            new = db.Library.from_json(json.dumps(js))
            new.created = datetime.datetime.utcnow()
            new.lifestages = lifestages
            new.build_keywords()
            new.name = "%s (imported %s)" % (new.name, new.created.isoformat())
            new.save()
            saved_items.append(str(new['_id']))

        if len(entry_list) == 1:
            if format == 'html':
                flash("Library item imported")
                return redirect(url_for('index'))
            elif format == 'json':
                return jsonify( { 'results' : saved_items} )
        elif len(entry_list > 1):
            if format == 'html':
                flash("%s library items imported" % len(entry_list))
                return redirect(url_for('index'))
            elif format == 'json':
                return jsonify( { 'results' : saved_items} )
        else:
            message = "No library items found in import, please try again"
            if format == 'html':
                flash(message)
                return redirect(url_for('index'))
            elif format == 'json':
                return jsonify( { 'results' : message } )

    return redirect(url_for('index'))


@app.route('/library', methods=['GET'])
@app.route('/library.<string:format>', methods=['GET'])
def list_library(format=None):

    if format != 'json':
        format = 'html'

    only_owned = bool(request.args.get("owned", False))

    # retrieve entries marked as public and that belong to the user
    if format == 'html':
        email = session.get('user_email', None)
    elif format == 'json':
        email = request.args.get("email", None)

    user = db.User.find_one({ 'email' : email })

    # We should paginate here
    entries = list(retrieve_all(user=user, only_owned=only_owned))

    if format == 'html':
        if len(entries) < 1:
            flash('No entries exist in the library')
        return render_template('library_list.html', libraries=entries)
    elif format == 'json':
        ls = [entry.simplified_json() for entry in entries]
        return jsonify( { 'results' : ls } )


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
            geo_string = geo_string.lstrip('(').rstrip(')')
            point_array = geo_string.split('),(')
            try:
                for pt in filter(None, point_array):
                    pt = pt.split(',')
                    pts.append((float(pt[1].strip()),float(pt[0].strip())))
                # Create the polygonts)
                geo_positional_data = unicode(Polygon(pts).wkt)
            except:
                app.logger.warning("Could not build Polygon from: %s" % pts)

        entry = db.Library()
        form.populate_obj(entry)

        entry['geometry'] = geo_positional_data
        entry['created'] = datetime.datetime.utcnow()
        entry['user'] = session['user_email'] # Safe because of @login_required decorator

        if entry.local_validate() is False:
            flash('Library with a name: %s and creator: %s already exists, please change the name to create' % (entry.name, entry.user))
        else:
            entry.build_keywords()
            db.libraries.ensure_index('_keywords')
            entry.save()

            # rebuild the indexes
            db.libraries.reindex()
                
            flash('Created library entry %s' % str(entry._id))
            return redirect(url_for('detail_view', library_id=entry._id ))

    return render_template('library_wizard.html', form=form)


@app.route('/library/<ObjectId:library_id>/reorder_lifestages', methods=['PUT'])
@login_required
def reorder_lifestages(library_id):
    # Get objects
    entry = db.Library.find_one({'_id':library_id})
    user = db.User.find_one({ 'email' : session.get("user_email")})

    if entry is None:
        flash('Cannot find ' + str(library_id) + ' for editing')
        return redirect(url_for('index'))

    # Permissions
    if not authorize_entry_write(entry=entry, user=user):
        flash("Not authorized edit this library item")
        return redirect(url_for('index'))

    lifestage_ids = request.form.get('lifestages').split(',')

    entry.lifestages = []
    for lfid in lifestage_ids:
        ls = db.LifeStage.find_one({'_id': ObjectId(lfid)})
        entry.lifestages.append(ls)

    entry.save()

    return jsonify({"results" : "success" })


@app.route('/library/<ObjectId:library_id>/edit', methods=['GET','POST'])
@login_required
def library_edit_wizard(library_id):
    # Get objects
    entry = db.Library.find_one({'_id':library_id})
    user = db.User.find_one({ 'email' : session.get("user_email")})

    if entry is None:
        flash('Cannot find ' + str(library_id) + ' for editing')
        return redirect(url_for('index'))

    # Permissions
    if not authorize_entry_write(entry=entry, user=user):
        flash("Not authorized edit this library item")
        return redirect(url_for('index'))

    form = BaseWizard(request.form, obj=entry)
    
    if request.method == 'POST' and form.validate():

        form.populate_obj(entry)

        # Setup the polygon
        geo_positional_data = None
        if request.form.get('geo') is not None:
            pts = []
            geo_string = request.form.get('geo')
            geo_string = geo_string.lstrip('(').rstrip(')')
            point_array = geo_string.split('),(')
            try:
                for pt in filter(None, point_array):
                    pt = pt.split(',')
                    pts.append((float(pt[1].strip()),float(pt[0].strip())))
                # Create the polygon
                geo_positional_data = unicode(Polygon(pts).wkt)
            except:
                app.logger.warning("Could not build Polygon from: %s" % pts)

        entry['geometry'] = geo_positional_data
        entry['created'] = datetime.datetime.utcnow()
        entry['user'] = session['user_email'] # Safe because of @login_required decorator

        if entry.local_validate() is False:
            flash('Library with a name: %s and creator: %s already exists, please change the name to edit' % (entry.name, entry.user))
        else:
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
