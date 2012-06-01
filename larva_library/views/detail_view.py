from flask import redirect, url_for, render_template, flash, session, request
from larva_library import app, db
from bson import ObjectId

@app.route('/detail')
def detail_view():
	entry_id = request.args.get('entry_id')

	if entry_id is None:
		flash('Recieved an entry without an id')
		return redirect(url_for('index'))
	
	entry = db.Library.find_one({'_id':ObjectId(entry_id)})

	if entry is None:
		flash('Cannot find object ' + str(entry_id))
		return redirect(url_for('index'))

	return render_template('library_detail.html', entry=entry)