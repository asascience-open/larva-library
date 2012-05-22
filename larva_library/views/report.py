from flask import Module, request, url_for, render_template, redirect
from larva_library import db, app

@app.route('/')
def show_reports():
    reports = list(db.reports.Report.find())
    return render_template('show_reports.html', reports=reports)

@app.route('/add', methods=['POST'])
def add_report():
    report = db.reports.Report()
    report['currents'] = request.form['currents']
    report['winds'] = request.form['winds']
    report['waves'] = request.form['waves']
    report['comments'] = request.form['comments']
    report.save()
    return redirect(url_for('show_reports'))

@app.route('/manage')
def add_report():
    report = db.reports.Report()
    report['currents'] = request.form['currents']
    report['winds'] = request.form['winds']
    report['waves'] = request.form['waves']
    report['comments'] = request.form['comments']
    report.save()
    return redirect(url_for('show_reports'))