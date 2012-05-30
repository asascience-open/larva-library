from flask import url_for, request, redirect, flash
from larva_library import app, db
from larva_library.models.library import LibrarySearch

@app.route("/library/search", methods=["POST"])
def library_search():
	form = LibrarySearch(request.form)

	if form.search_name.data is None or form.search_name.data == '':
		flash('Improper search name')
		return redirect(url_for('index'))

	results = db.Library.find({'Name':form.search_name.data})

	result_string=''

	for result in results:
		result_string = result_string + result['Name'] + ','

	return redirect(url_for('index', results=result_string))
