from larva_library import db, app
from larva_library.models.library import WizardFormOne, WizardFormTwo, WizardFormThree
from flask import request, url_for, redirect, render_template, flash, session
import datetime

@app.route('/wizard/page/1', methods=['GET','POST'])
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

@app.route('/wizard/page/2', methods=['GET','POST'])
def wizard_page_two():
    form = WizardFormTwo(request.form)

    if session.get('new_entry') is None:
        # throw exception that we did not go in order
        flash('Please start the wizard from the index, page 2')
        return redirect(url_for('index'))
    
    elif request.method == 'POST' and form.validate():
        lib = session['new_entry']
        lib['Keywords'] = form.keywords.data
        lib['Geography'] = form.geography.data
        session['new_entry'] = lib
        # copy dict into the Library structure
        return redirect(url_for('wizard_page_three'))
    
    return render_template('wizard_page_two.html', form=form)

@app.route('/wizard/page/3', methods=['GET','POST'])
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
        
    