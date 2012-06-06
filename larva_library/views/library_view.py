from flask import url_for, request, redirect, flash, render_template, session
from larva_library import app, db
from larva_library.models.library import LibrarySearch
from larva_library.models.library import WizardFormOne, WizardFormTwo, WizardFormThree
from shapely.wkt import dumps, loads
from shapely.geometry import Point
from bson import ObjectId
import datetime

@app.route('/library/detail')
def detail_view():
    entry_id = request.args.get('entry_id')

    if entry_id is None:
        flash('Recieved an entry without an id')
        return redirect(url_for('index'))

    entry = db.Library.find_one({'_id':ObjectId(entry_id)})

    if entry is None:
        flash('Cannot find object ' + str(entry_id))
        return redirect(url_for('index'))

    # return the positional data into usable points for markers on google maps
    marker_poisitions = []
    # load the point data and put the positions into tuples
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
    	flash('Improper search keywords')
    	return redirect(url_for('index'))

    query = dict()
    _keyword_query = dict()
    _keystr = form.search_keywords.data.rstrip(',')
    query['_keywords'] = {'$all':_keystr.split(',')}
    if form.user_owned.data == True and session.get('user_email') is not None:
    		query['User'] = session['user_email']

    results = db.Library.find(query)
    if results.count() == 0:
        flash('Unable to find entry(ies)')

    result_string=''

    for result in results:
    	result_string = result_string + result['Name'] + ','

    return redirect(url_for('index', results=result_string))

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
@app.route('/library/edit/<library_name>')
def edit_entry(library_name):
    if library_name is None:
        flash('Cannot edit empty entry, try making a new one instead')
        return redirect(url_for('index'))

    entry = db.Library.find_one({'User':session['user_email'], 'Name':library_name})
    if entry is None:
        flash('Cannot find ' + library_name + ' for current user, please make sure you have privileges necessary to edit the entry')
        return redirect(url_for('index'))

    #Pass along entry as form
    return redirect(url_for('wizard_page_one', form=entry))

########################################################
#
#	Wizard Pages
#
########################################################
@app.route('/library/wizard/page/1', methods=['GET','POST'])
def wizard_page_one():
    form = WizardFormOne(request.form)

    # temporary fix for removing current library in session, to start over
    if session.get('new_entry') is not None:
        session.pop('new_entry')
        
    if request.method == 'POST' and form.validate():
        if session.get('new_entry') is None:
            lib = dict()
            lib['Name'] = form.lib_name.data
            lib['Genus']= form.genus.data
            lib['Species'] = form.species.data
            lib['Common_Name'] = form.common_name.data
            # add to our _keywords
            _keywords = []
            _keywords.extend(lib['Name'].split(' '))
            _keywords.extend(lib['Genus'].split(' '))
            _keywords.extend(lib['Species'].split(' '))
            _keywords.extend(lib['Common_Name'].split(' '))
            lib['_keywords'] = _keywords
            session['new_entry'] = lib
            
        return redirect(url_for('wizard_page_two'))

    return render_template('wizard_page_one.html', form=form)

@app.route('/library/wizard/page/2', methods=['GET','POST'])
def wizard_page_two():
    wiz_form = WizardFormTwo(request.form)

    geo_positional_data = []

    if request.form.get('geo') is not None:
        geo_array = wiz_form.geo.data.split('ngp')
        # remove last member of the array (it will be empty)
        geo_array.pop()
        # for each item in the array we need to load it as a point and then print its wkt
        for point in geo_array:
            # strip any '() '
            point = point.replace('(','')
            point = point.replace(')','')
            point = point.replace(' ','')
            # split into two values
            point_array = point.split(',')
            # now create a Point with the two valus
            temp_point = Point(float(point_array[0]),float(point_array[1]))
            # add to our data
            geo_positional_data.append(unicode(temp_point.wkt))

    if session.get('new_entry') is None:
        # throw exception that we did not go in order
        flash('Please start the wizard from the index, page 2')
        return redirect(url_for('index'))

    elif request.method == 'POST' and wiz_form.validate():
        lib = session['new_entry']
        lib['Keywords'] = wiz_form.keywords.data
        lib['GeoKeywords'] = wiz_form.geo_keywords.data
        lib['Geometry'] = geo_positional_data
        # add the keywords to the internal keywords
        for kywrd in wiz_form.keywords.data:
            lib['_keywords'].append(kywrd)
        
        session['new_entry'] = lib
        # copy dict into the Library structure
        return redirect(url_for('wizard_page_three'))

    return render_template('wizard_page_two.html', form=wiz_form)

@app.route('/library/wizard/page/3', methods=['GET','POST'])
def wizard_page_three():
    form = WizardFormThree(request.form)

    if session.get('new_entry') is None:
        # throw exception that we did not go in order
        flash('Please start the wizard from the index, page 3')

        if session.get('count') is not None:
            session.pop('count')

        return redirect(url_for('index'))

    elif request.args.get('add_stage') is not None:
        # increment our lifestage counter and a new entry
        count = 0
        if session.get('count') is not None:
            count = session.get('count')

        count += 1
        for i in range(0,count):
            form.lifestages.append_entry()

        session['count'] = count

    elif request.method == 'POST' and form.validate():
        lib = session['new_entry']
        lib['LifeStages'] = form.lifestages.data
        # get our datetime
        lib['Created'] = datetime.datetime.utcnow()
        # save ourself as primary user
        lib['User'] = session['user_email']
        session['new_entry'] = lib

        m_lib = db.Library()
        m_lib.copy_from_dictionary(lib)
        # ensure index our keywords
        db.libraries.ensure_index('_keywords')
        m_lib.save()

        # rebuild the index
        db.libraries.reindex()

        if session.get('count') is not None:
            session.pop('count')

        flash('Successfully added entry ' + str(m_lib._id))

        return redirect(url_for('index'))

    elif session.get('count') is not None:
        session.pop('count')

    return render_template('wizard_page_three.html', form=form)
        
