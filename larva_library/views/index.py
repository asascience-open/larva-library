from flask import render_template, redirect, url_for, session, flash, request
from larva_library import app, db
from larva_library.models.library import LibrarySearch

@app.route('/', methods=['GET', 'POST'])
def index():
    form = LibrarySearch(request.form)
    user = session.get('user_email', None)
    results = None
    libraries = None

    # A search was submitted
    if request.method == 'POST':
      result = request.form.get('search_keywords')
      result = result.rstrip(',')
      results = result.split(',')

    if user is not None:
        libraries = list(db.Library.find({'User':user}))
    
    return render_template('index.html', results=results, libraries=libraries, form=form)


#testing
@app.route('/testing/set/email', methods=['POST'])
def user_email():
    if request.form.get('user_email') is not None:
        session['user_email'] = request.form.get('user_email')
        flash('TEST: set user_email')
    return render_template('layout.html')