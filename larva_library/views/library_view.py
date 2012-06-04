from flask import url_for, request, redirect, flash, render_template, session
from larva_library import app, db
from larva_library.models.library import LibrarySearch
from larva_library.models.library import WizardFormOne, WizardFormTwo, WizardFormThree
from shapely.wkt import dumps, loads
from shapely.geometry import Point
import datetime

@app.route("/library/search", methods=["POST"])
def library_search():
	form = LibrarySearch(request.form)

	if form.search_name.data is None or form.search_name.data == '':
		flash('Improper search name')
		return redirect(url_for('index'))

	query = dict()
	query['Name'] = form.search_name.data
	if form.user_owned.data == True and session.get('user_email') is not None:
			query['User'] = session['user_email']

	results = db.Library.find(query)

	result_string=''

	for result in results:
		result_string = result_string + result['Name'] + ','

	return redirect(url_for('index', results=result_string))

@app.route('/library')
def list_library():
	# retrieve entire db and pass it to the html
	libraries = db.Library.find()
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
            session['new_entry'] = lib
            
        return redirect(url_for('wizard_page_two'))
    
    return render_template('wizard_page_one.html', form=form)

@app.route('/library/wizard/page/2', methods=['GET','POST'])
def wizard_page_two():
    wiz_form = WizardFormTwo(request.form)
    # if request.form is not None:
    #     flash(request.form)
    #     flash(request.form.items())

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
        lib['Geometry'] = geo_positional_data
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
        m_lib.save()

        if session.get('count') is not None:
            session.pop('count')

        return redirect(url_for('index'))

    elif session.get('count') is not None:
        session.pop('count')
    
    return render_template('wizard_page_three.html', form=form)
        
    