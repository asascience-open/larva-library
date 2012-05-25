from flask import request, url_for, render_template, redirect
from larva_library import db, app
from larva_library.models.user import User

@app.route('/users')
def show_users():
    users = list(db.User.find())
    return render_template('show_users.html', users=users)
