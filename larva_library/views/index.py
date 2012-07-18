from flask import render_template, redirect, url_for, session, flash, request
from larva_library import app, db
from larva_library.models.library import LibrarySearch

@app.route('/', methods=['GET'])
def index():
    form = LibrarySearch(request.form)
    user = session.get('user_email', None)
    libraries = None

    if user is not None:
        libraries = list(db.Library.find({'User':user}))
    
    return render_template('index.html', libraries=libraries, form=form)