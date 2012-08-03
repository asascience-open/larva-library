from flask import request, url_for, render_template, redirect
from larva_library import db, app
from larva_library.models.user import User
from larva_library.views.utils import admin_login_required

@app.route('/users')
@admin_login_required
def show_users():
    users = list(db.User.find())
    return render_template('show_users.html', users=users)
