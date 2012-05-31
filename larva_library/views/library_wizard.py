from larva_library import db, app
from larva_library.models.library import WizardFormOne, WizardFormTwo, WizardFormThree
from flask import request, url_for, redirect, render_template, flash, session
import datetime

@app.route('/wizard/page/1', methods=['GET','POST'])
def wizard_page_one():
    form = WizardFormOne(request.form)
    
    # temporary fix for removing current library in session, to start over
    if session.get('current_library') is not None:
        session.pop('current_library')
        
    if request.method == 'POST' and form.validate():
        if session.get('current_library') is None:
            lib = dict()
            lib['Name'] = form.lib_name.data
            lib['Genus']= form.genus.data
            lib['Species'] = form.species.data
            lib['Common_Name'] = form.common_name.data
            session['current_library'] = lib
            
        return redirect(url_for('wizard_page_two'))
    
    return render_template('wizard_page_one.html', form=form)

@app.route('/wizard/page/2', methods=['GET','POST'])
def wizard_page_two():
    form = WizardFormTwo(request.form)

    if session.get('current_library') is None:
        # throw exception that we did not go in order
        flash('Please start the wizard from the index, page 2')
        return redirect(url_for('index'))
    
    elif request.method == 'POST' and form.validate():
        lib = session['current_library']
        lib['Keywords'] = form.keywords.data
        lib['Geography'] = form.geography.data
        session['current_library'] = lib
        # copy dict into the Library structure
        return redirect(url_for('wizard_page_three'))
    
    return render_template('wizard_page_two.html', form=form)

@app.route('/wizard/page/3', methods=['GET','POST'])
def wizard_page_three():
    form = WizardFormThree(request.form,min_fields=3)
    
    if session.get('current_library') is None:
        # throw exception that we did not go in order
        flash('Please start the wizard from the index, page 3')
        return redirect(url_for('index'))
    
    elif request.method == 'POST' and form.validate():
        lib = session['current_library']
        lib['LifeStages'] = form.lifestages.data
        # get our datetime
        lib['Created'] = datetime.datetime.utcnow()
        # save ourself as primary user
        lib['User'] = session['user_email']
        session['current_library'] = lib
        m_lib = db.Library()
        m_lib.copy_from_dictionary(lib)
        m_lib.save()
        return redirect(url_for('index'))
    
    return render_template('wizard_page_three.html', form=form)
        
    