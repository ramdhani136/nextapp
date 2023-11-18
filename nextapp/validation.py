import frappe
import sys
import json

def success_format(doc):
	data = dict()
	data['code'] = 200
	data['data'] = doc
	return data

def error_format(err):
	data = dict()

	if type(err) == frappe.exceptions.AuthenticationError:
		data['code'] = 440
		data['error'] = err[0]
	elif type(err) == frappe.exceptions.ValidationError:
		data['code'] = 417
		data['error'] = err[0]
	elif type(err) == frappe.exceptions.DoesNotExistError:
		data['code'] = 404
		data['error'] = err[0]
	elif type(err) == frappe.exceptions.PermissionError:
		data['code'] = 403
		data['error'] = err[0]
	elif type(err) == frappe.exceptions.MandatoryError:
		data['code'] = 400
		data['error'] = err[0]
	else:
		data['code'] = 500
		data['error'] = err
	return data

@frappe.whitelist(allow_guest=True)
def test_validation():
	try:
		frappe.throw("baca aku")
	except:
		return error_format(sys.exc_info()[0])

@frappe.whitelist(allow_guest=False)
def validate_get_list(doctype):
	try:
		tryFetch = frappe.get_list(doctype)
		return "success"
	except:
		return error_format(sys.exc_info()[0])

@frappe.whitelist(allow_guest=False)
def insert_doctype():
	try:
		data = json.loads(frappe.request.data.decode('utf-8'))
		doc = frappe.get_doc(data)
		doc.insert()
		return doc
	except:
		return error_format(sys.exc_info()[0])
