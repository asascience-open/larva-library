from flask import render_template, redirect, url_for, session, flash, request
from larva_library import app, db
from larva_library.models.library import LibrarySearch

@app.route('/')
def index():
    form = LibrarySearch(request.form)

    user = session.get('user_email')

    if request.args.get('results') is not None:
      result = request.args.get('results')
      result = result.rstrip(',')
      results = result.split(',')
      
      return render_template('index.html', results=results, form=form, loggedin=user)

    if user is not None:
        libraries = list(db.Library.find({'User':user}))
        return render_template('index.html', libraries=libraries, form=form, loggedin=user)

    else:
        return render_template('index.html', form=form, loggedin=user)


#testing
@app.route('/testing/set/email', methods=['POST'])
def user_email():
    if request.form.get('user_email') is not None:
        session['user_email'] = request.form.get('user_email')
        flash('TEST: set user_email')
    return render_template('layout.html')