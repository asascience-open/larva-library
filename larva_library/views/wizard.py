from flask import url_for, request, redirect, flash, render_template, session
from larva_library import app, db
from larva_library.models.library import BaseWizard, LifeStageWizard
from larva_library.views.utils import login_required, str_to_num
from shapely.geometry import Polygon
from shapely.wkt import loads
import datetime
import json
import time
import pytz
from dateutil.parser import parse

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

@app.route('/library/<ObjectId:library_id>/lifestage', methods=['GET','POST'])
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
        lifestage.vss = form.vss.data
        lifestage.duration = form.duration.data
        lifestage.diel = [] 
        lifestage.taxis = []

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

    return render_template('lifestage_wizard.html', form=form, entry=library_id)