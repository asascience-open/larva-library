from flask import url_for, request, redirect, flash, render_template, send_file
from larva_library import app, db
from larva_library.models.library import LibrarySearch, Library
from bson import ObjectId
from larva_library.views.library import retrieve_public_entries, retrieve_entries_for_user
import StringIO

@app.route('/library.json', methods=['GET'])
def larva_json_service():
	# overhaul: query vars to look for library_ids, terms, email, user_owned_only
	json_result = dict()
	library_list = list()
	entry_json_list = list()

	id_list = request.args.get("library_ids")
	email = request.args.get("email")
	terms = request.args.get("terms")
	user_only = request.args.get("user_owned_only", default=False)

	if id_list is not None:
		library_list = retrieve_by_id(id_list, email)

	elif terms is not None:
		library_list = retrieve_by_terms(terms, email, user_only)

	else:
		library_list = retrieve_all(email)

	if len(library_list) == 0:
		flash("Unable to find any entries matching criterion, please try again")
		return redirect(url_for('index.html'))

	# collect all of the json entries into one list
	for entry in library_list:
	   entry_json_list.append(entry.to_json())

	json_result['library_results'] = entry_json_list

	#create a string stream to act as a temporary file for downloading the json
	stringStream = StringIO.StringIO()
	stringStream.write(json_result)
	# ensure that the stream starts at the beginning for the read to file
	stringStream.seek(0)

	return send_file(stringStream, attachment_filename="library_search.json", as_attachment=True)

def retrieve_by_id(entry_ids, email=None):
	entry_list = list()

	if entry_ids is None:
		flash("Emtpy id set received")

	else:
		entry_ids = [x for x in entry_ids.split(',') if x]
		# create a query dict from the ids
		query = dict()
		tlist = list()

		for libid in entry_ids:
			tlist.append(dict(_id=ObjectId(libid.encode('ascii','ignore'))))

		query["$or"] = tlist
		results = db.Library.find(query)
		for entry in results:
			entry_list.append(entry)

	return entry_list

def retrieve_by_terms(terms, email=None, user_only=False):
	entry_list = list()

	if terms is None:
		# flash error and return empty result
		flash("Emtpy search params")

	else:
		# terms should be a comma deliminated string; remove any trailing commas
		terms = terms.rstrip(',')
		keywords = {'$all':_keystr.split(',')}

		if email is not None:
			search_result = retrieve_entries_for_user(email, keywords=keywords)
			for result in search_result:
				entry_list.append(result)

		if user_only is False:
			search_result = retrieve_public_entries(keywords)
			for result in search_result:
				if result not in entry_list:
					entry_list.append(result)

	return entry_list

def retrieve_all(email=None, user_only=False):
	entry_list = list()

	# retrieve user and public entries; add each entry's json representation
	if email is not None:
		entries = retrieve_entries_for_user(email)
		for entry in entries:
			entry_list.append(entry)

	#get the master/public list and add it
	if user_only is False:
		entries = retrieve_public_entries()
		for entry in entries:
			if entry not in entry_list:
				entry_list.append(entry)

	return entry_list