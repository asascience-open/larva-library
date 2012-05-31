from flask import redirect, url_for, request, flash, render_template
from larva_library import app, db

@app.route('/library')
def list_library():
	# retrieve entire db and pass it to the html
	libraries = db.Library.find()
	return render_template('library_list.html', libraries=libraries)