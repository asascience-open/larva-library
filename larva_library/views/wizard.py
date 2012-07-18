from flask import url_for, request, redirect, flash, render_template, session
from larva_library import app, db
from larva_library.models.library import BaseWizard, LifeStageWizard
from larva_library.views.utils import login_required
from shapely.geometry import Polygon
import datetime

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
            for pt in point_array:
                pt = pt.split(",")
                pts.append((float(pt[1].replace(")","")),float(pt[0].replace("(",""))))
            # Create the polygon
            geo_positional_data = unicode(Polygon(pts).wkt)

        lib = dict()
        lib['Name'] = form.name.data
        lib['Genus']= form.genus.data
        lib['Species'] = form.species.data
        lib['Common_Name'] = form.common_name.data
        lib['Keywords'] = form.keywords.data
        lib['GeoKeywords'] = form.geo_keywords.data
        lib['Geometry'] = geo_positional_data
        lib['Created'] = datetime.datetime.utcnow()
        lib['User'] = session['user_email'] # Safe because of @login_required decorator

        # add to our _keywords
        _keywords = []
        _keywords.extend(lib['Name'].split(' '))
        _keywords.extend(lib['Genus'].split(' '))
        _keywords.extend(lib['Species'].split(' '))
        _keywords.extend(lib['Common_Name'].split(' '))
        _keywords.extend(lib['Keywords'])
        _keywords.extend(lib['GeoKeywords'])
        lib['_keywords'] = _keywords

        entry = db.Library()
        entry.copy_from_dictionary(lib)
        db.libraries.ensure_index('_keywords')
        entry.save()

        # rebuild the indexes
        db.libraries.reindex()
            
        flash('Created library entry %s' % str(entry._id))
        return redirect(url_for('detail_view', library_id=entry._id ))

    return render_template('library_wizard.html', form=form)


@app.route('/library/<ObjectId:library_id>/lifestage_wizard', methods=['GET','POST'])
@login_required
def lifestage_wizard(library_id):

    # Be sure the logged in user has access to this library item
    entry = db.Library.find_one({'_id': library_id})
    if entry.User != session['user_email']:
        flash("Not authorized to add lifestages to this library item")

    form = LifeStageWizard(request.form)

    if request.method == 'POST' and form.validate():

        lib = dict()
        lib['name'] = form.name.data
        lib['vss'] = form.vss.data
        lib['duration'] = form.duration.data

        entry.Lifestages.append(lib)
        entry.save()

        flash('Created LifeStage')
        return redirect(url_for('detail_view', library_id=entry._id ))

    return render_template('lifestage_wizard.html', form=form, entry=library_id)