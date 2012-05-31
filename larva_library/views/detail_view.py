from flask import redirect, url_for, render_template, flash, session, request
from larva_library import app, db

@app.route('/detail')
def detail_view():
	entry_name = request.args.get('entry_name')
	if entry_name is None:
		flash('Cannot find an entry without a name')
		return redirect(url_for('index'))
	else:
	    entry = db.Library.find_one({'User':session['user_email'],'Name':entry_name})
	    if entry is None:
	        flash('Cannot find ' + library_name + ' for user ' + session['user_email'])
	        return redirect(url_for('index'))
	    else:
	        return render_template('library_detail.html', entry=entry)