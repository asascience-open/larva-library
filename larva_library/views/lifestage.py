from flask import url_for, request, redirect, flash, render_template, session
from larva_library import app, db
from larva_library.views.utils import login_required
from larva_library.models.library import LifeStageWizard
import datetime
import json
import time
import pytz
from dateutil.parser import parse

@app.route('/library/<ObjectId:library_id>/lifestages/<ObjectId:lifestage_id>/clone', methods=['GET'])
@login_required
def clone_lifestage(library_id, lifestage_id):

    # Be sure the logged in user has access to this library item
    entry = db.Library.find_one({'_id': library_id})
    if entry.user != session['user_email']:
        flash("Not authorized to clone lifestages for this library item")

    entry = db.Library.find_one({'_id': library_id})

    # Iterate over lifestages and match on the ID
    for lifestage in entry.lifestages:
        if lifestage['_id'] == lifestage_id:
            # Populate newlifestage
            newlifestage = lifestage.clone()
            newlifestage.save()
            # Add copy of 'lifestage' to library.lifestages
            entry.lifestages.append(newlifestage)
            entry.save()
            flash('Cloned LifeStage')
            return redirect(url_for('detail_view', library_id=entry._id ))

    flash('Could not clone LifeStage')
    return redirect(url_for('detail_view', library_id=entry._id ))


@app.route('/library/<ObjectId:library_id>/lifestages/<ObjectId:lifestage_id>/delete', methods=['GET'])
@login_required
def delete_lifestage(library_id, lifestage_id):

    # Be sure the logged in user has access to this library item
    entry = db.Library.find_one({'_id': library_id})
    if entry.user != session['user_email']:
        flash("Not authorized to clone lifestages for this library item")

    entry = db.Library.find_one({'_id': library_id})
    for lifestage in entry.lifestages:
        if lifestage['_id'] == lifestage_id:
            entry.lifestages.remove(lifestage)
            entry.save()
            flash('Deleted LifeStage')
            return redirect(url_for('detail_view', library_id=entry._id ))

    flash('Could not delete LifeStage')
    return redirect(url_for('detail_view', library_id=entry._id ))


@app.route('/library/<ObjectId:library_id>/lifestages/<ObjectId:lifestage_id>/edit', methods=['GET','POST'])
@login_required
def edit_lifestage(library_id, lifestage_id):

    # Get library object
    entry = db.Library.find_one({'_id':library_id})
    if entry is None:
        flash('Cannot find library ' + str(library_id) + ' for editing')
        return redirect(url_for('index'))

    # Permissions
    if session.get('user_email', None) != entry.user:
        flash('%s does not have permission to edit this entry')
        return redirect(url_for('index'))

    # Get the lifestage object we are editing
    old_lifestage = None
    for lifestage in entry.lifestages:
        if lifestage['_id'] == lifestage_id:
            old_lifestage = lifestage

    if old_lifestage is None:
        flash('Cannot find lifestage ' + str(lifestage_id) + ' for editing')
        return redirect(url_for('detail_view', library_id=entry._id ))

    form = LifeStageWizard(request.form, obj=lifestage)

    if request.method == 'POST' and form.validate():

        lifestage = db.LifeStage()
        lifestage.name = form.name.data
        lifestage.duration = form.duration.data
        lifestage.notes = form.notes.data
        lifestage.diel = [] 
        lifestage.taxis = []
        lifestage.capability = None

        # Capability
        if form.capability.data:
            c = db.Capability()
            c.vss = float(form.vss.data)
            c.variance = float(form.variance.data)
            c.swim_turning = form.swim_turning.data
            c.nonswim_turning = form.nonswim_turning.data
            c.save()
            lifestage.capability = c

        # Diel
        if form.diel_data.data and len(form.diel_data.data) > 0:

            parsed_diel = json.loads(form.diel_data.data)
            for diel_data in parsed_diel:

                d = db.Diel()
                d.type = unicode(diel_data['diel_type'])
                d.min = float(diel_data['min'])
                d.max = float(diel_data['max'])

                if d.type == u'cycles':
                    d.cycle = unicode(diel_data['cycle'])
                    d.plus_or_minus = unicode(diel_data['plus_or_minus'])
                    d.hours = int(diel_data['hours'])
                elif d.type == u'specifictime':
                    t = parse("%s %s" % (diel_data['diel_time'], diel_data['timezone']))
                    try:
                        d.time = pytz.utc.normalize(t).replace(tzinfo=None)
                    except:
                        # already in GMT
                        d.time = t
                    
                d.save()
                lifestage.diel.append(d)
            
        if form.taxis_data.data and len(form.taxis_data.data) > 0:

            parsed_taxis = json.loads(form.taxis_data.data)
            for taxis_data in parsed_taxis:

                t = db.Taxis()            
                t.variable = taxis_data['variable']
                t.units = taxis_data['units']
                t.min = float(taxis_data['min'])
                t.max = float(taxis_data['max'])
                t.gradient = float(taxis_data['gradient'])

                t.save()
                lifestage.taxis.append(t)

        lifestage.save()


        # Remove lifestage we are editing
        entry.lifestages.remove(old_lifestage)

        # Add new lifestage
        entry.lifestages.append(lifestage)
        entry.save()

        flash('Edited LifeStage')
        return redirect(url_for('detail_view', library_id=entry._id ))

    else:
        diels = []
        for diel in lifestage.diel:
            diels.append(diel.to_data())
        form.diel_data.data = json.dumps(diels)
        
        taxis = []
        for tx in lifestage.taxis:
            taxis.append(tx.to_data())
        form.taxis_data.data = json.dumps(taxis)

        form.vss.data = lifestage.capability.vss
        form.variance.data = lifestage.capability.variance
        form.swim_turning.data = lifestage.capability.swim_turning
        form.nonswim_turning.data = lifestage.capability.nonswim_turning

    return render_template('lifestage_wizard.html', form=form)


@app.route('/library/<ObjectId:library_id>/lifestages', methods=['GET','POST'])
@login_required
def lifestage_wizard(library_id):

    # Be sure the logged in user has access to this library item
    entry = db.Library.find_one({'_id': library_id})
    if entry.user != session['user_email']:
        flash("Not authorized to add lifestages to this library item")

    form = LifeStageWizard(request.form)

    if request.method == 'POST' and form.validate():

        lifestage = db.LifeStage()
        lifestage.name = form.name.data
        lifestage.duration = form.duration.data
        lifestage.notes = form.notes.data
        lifestage.diel = [] 
        lifestage.taxis = []
        lifestage.capability = None

        # Capability
        if form.capability.data:
            c = db.Capability()
            c.vss = float(form.vss.data)
            c.variance = float(form.variance.data)
            c.swim_turning = form.swim_turning.data
            c.nonswim_turning = form.nonswim_turning.data
            c.save()
            lifestage.capability = c

        # Diel
        if form.diel_data.data and len(form.diel_data.data) > 0:

            parsed_diel = json.loads(form.diel_data.data)
            for diel_data in parsed_diel:

                d = db.Diel()
                d.type = unicode(diel_data['diel_type'])
                d.min = float(diel_data['min'])
                d.max = float(diel_data['max'])

                if d.type == u'cycles':
                    d.cycle = unicode(diel_data['cycle'])
                    d.plus_or_minus = unicode(diel_data['plus_or_minus'])
                    d.hours = int(diel_data['hours'])
                elif d.type == u'specifictime':
                    t = parse("%s %s" % (diel_data['diel_time'], diel_data['timezone']))
                    d.time = pytz.utc.normalize(t).replace(tzinfo=None)
                    
                d.save()
                lifestage.diel.append(d)
            
        if form.taxis_data.data and len(form.taxis_data.data) > 0:

            parsed_taxis = json.loads(form.taxis_data.data)
            for taxis_data in parsed_taxis:

                t = db.Taxis()            
                t.variable = taxis_data['variable']
                t.units = taxis_data['units']
                t.min = float(taxis_data['min'])
                t.max = float(taxis_data['max'])
                t.gradient = float(taxis_data['gradient'])

                t.save()
                lifestage.taxis.append(t)

        lifestage.save()
        entry.lifestages.append(lifestage)
        entry.save()

        flash('Created LifeStage')
        return redirect(url_for('detail_view', library_id=entry._id ))

    return render_template('lifestage_wizard.html', form=form)