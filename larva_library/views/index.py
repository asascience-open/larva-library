from flask import render_template, redirect, url_for, session, flash, request, make_response
from larva_library import app, db
from larva_library.models.library import LibrarySearch

@app.route('/', methods=['GET'])
def index():
    form = LibrarySearch(request.form)
    user = session.get('user_email', None)
    libraries = None

    if user is not None:
        libraries = list(db.Library.find({'user':user}))
    
    return render_template('index.html', libraries=libraries, form=form)

@app.route('/crossdomain.xml', methods=['GET'])
def crossdomain():
    domain = """
    <cross-domain-policy>
        <allow-access-from domain="*"/>
        <site-control permitted-cross-domain-policies="all"/>
        <allow-http-request-headers-from domain="*" headers="*"/>
    </cross-domain-policy>
    """
    response = make_response(domain)
    response.headers["Content-type"] = "text/xml"
    return response
