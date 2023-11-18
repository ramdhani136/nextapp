from __future__ import unicode_literals
import frappe
import json
import hashlib
import time
import operator
from frappe.utils.file_manager import *
from nextapp.base import validate_method
from frappe.utils import get_fullname, get_request_session
from frappe import utils
import sys

# ERPNEXT
from erpnext.stock.get_item_details import get_item_details

# CUSTOM METHOD
from nextapp.app.helper import *
from api_integration.validation import *
from api_integration.validation import * 
from api_integration.validation import *

LIMIT_PAGE = 20
API_VERSION = 1.9

@frappe.whitelist(allow_guest=True)
def me():
	me = frappe.session
	return me


@frappe.whitelist(allow_guest=True)
def ping():
	return "pong"

@frappe.whitelist(allow_guest=True)
def version():
	data = dict()

	data["api_version"] = API_VERSION
	return data

# USER PERMISSION
@frappe.whitelist(allow_guest=False)
def get_user_permission():
	user = frappe.session.user

	data = dict()
	data['has_roles'] = frappe.db.sql("SELECT * FROM `tabHas Role` WHERE parent='{}'".format(user),as_dict=1)
	dataUser = frappe.db.sql("SELECT * FROM `tabUser` WHERE name='{}'".format(user),as_dict=1)
	if len(dataUser) > 0:
		data['user'] = dataUser[0] 
	data['user_permissions'] = frappe.db.sql("SELECT * FROM `tabUser Permission` WHERE user='{}'".format(user),as_dict=1)

	return data

# METADATA
@frappe.whitelist(allow_guest=False)
def get_metadata():

	data = dict()

	fetchCurrency = frappe.get_list("Currency",
					fields="symbol,name",
					order_by="name")
	data['currency'] = fetchCurrency

	#delivery note
	status = ['Draft', 'To Bill','To Bill','Completed','Cancelled','Closed']
	data['delivery_note'] = dict()
	dataDN = data['delivery_note']
	dataDN['count'] = dict()
	dataCount = dataDN['count']
	for stat in status:
		fetch = frappe.get_list("Delivery Note", 
							filters = 
							{
								"status": stat
							})
		dataCount[stat] = len(fetch)

	#sales order
	status = ['Draft', 'To Deliver and Bill','To Bill','To Deliver','Completed','Cancelled','Closed']
	data['sales_order'] = dict()
	dataSO = data['sales_order']
	dataSO['count'] = dict()
	dataCount = dataSO['count']
	for stat in status:
		fetch = frappe.get_list("Sales Order", 
							filters = 
							{
								"status": stat
							})
		dataCount[stat] = len(fetch)

	#sales order delivery status
	status = ['Not Delivered', 'Fully Delivered', 'Partly Delivered']
	for stat in status:
		fetch = frappe.get_list("Sales Order", 
							filters = 
							{
								"delivery_status": stat,
								"docstatus":1,
								"status":("not in",["Draft", "Closed", "Completed", "Cancelled"]) 
							})
		dataCount[stat] = len(fetch)

	#sales order billing status
	status = ['Not Billed','Fully Billed','Partly Billed']
	for stat in status:
		fetch = frappe.get_list("Sales Order", 
							filters = 
							{
								"billing_status": stat,
								"docstatus":1,
								"status":("not in",["Draft", "Closed", "Completed", "Cancelled"])
							})
		dataCount[stat] = len(fetch)

	so_data = frappe.get_list("Sales Order")
	dataCount['Total'] = len(so_data)


	#invoice
	status = ['Overdue','Unpaid','Paid','Return','Credit Note Issued','Cancelled']
	data['invoice'] = dict()
	dataINV = data['invoice']
	dataINV['count'] = dict()
	dataCount = dataINV['count']
	for stat in status:
		fetch = frappe.get_list("Sales Invoice", 
							filters = 
							{
								"status": stat
							})
		dataCount[stat] = len(fetch)
			

	#lead
	status = ['Lead','Open','Replied','Opportunity','Interested','Quotation','Lost Quotation','Converted','Do Not Contact']
	data['lead'] = dict()
	dataLead = data['lead']
	dataLead['count'] = dict()
	dataCount = dataLead['count']
	for stat in status:
		fetch = frappe.get_list("Lead", 
							filters = 
							{
								"status": stat
							})
		dataCount[stat] = len(fetch)

	dataCount['Quotation'] += len(frappe.get_list("Quotation",filters = {"status": ("IN", ['Submitted','Open']),"quotation_to": "Customer"}))
	dataCount['Converted'] += len(frappe.get_list("Quotation",filters = {"status": "Ordered","quotation_to": "Customer"}))
	dataCount['Opportunity'] += len(frappe.get_list("Opportunity",filters = {"status": "Open","opportunity_from": "Customer"}))


	#net sales
	week = 0
	data['daily_net_sales'] = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS net_sales, DATE_FORMAT(daily.day, '%e %b') AS posting_date FROM (SELECT DATE(NOW()) - INTERVAL (0 + {}) DAY AS day UNION ALL SELECT DATE(NOW()) - INTERVAL (1 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (2 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (3 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (4 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (5 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (6 + {}) DAY) daily LEFT JOIN (SELECT SUM(si.net_total) AS total, si.posting_date FROM `tabSales Invoice` si WHERE docstatus = 1 GROUP BY si.posting_date) sales ON sales.posting_date = daily.day;".format(week, week, week, week, week, week, week),as_dict=1)


	fetchPrintFormat = frappe.db.sql("SELECT name, doc_type FROM `tabPrint Format` WHERE disabled = 0",as_dict=1)

	data["print_format"] = fetchPrintFormat

	return data


@frappe.whitelist(allow_guest=False)
def get_sales_by_person():
	data = dict()
	today = utils.today()
	data["sales_person_all_time"] = frappe.db.sql("SELECT st.sales_person AS 'person_name', SUM(si.rounded_total * si.conversion_rate) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE si.docstatus = 1 GROUP BY st.sales_person ORDER BY total_sales DESC", as_dict=True)
	data["sales_person_day"] = frappe.db.sql("SELECT st.sales_person AS 'person_name', SUM(si.rounded_total * si.conversion_rate) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE si.docstatus = 1 AND si.posting_date = '{}' GROUP BY st.sales_person ORDER BY total_sales DESC".format(today), as_dict=True)
	data["sales_person_month"] = frappe.db.sql("SELECT st.sales_person AS 'person_name', SUM(si.rounded_total * si.conversion_rate) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE si.docstatus = 1 AND DATE_FORMAT(si.posting_date, '%Y-%m') = DATE_FORMAT('{}', '%Y-%m') GROUP BY st.sales_person ORDER BY total_sales DESC".format(today), as_dict=True)
	return data

@frappe.whitelist(allow_guest=False)
def attach():
	response = {}

	req = frappe.local.form_dict
	if (req == None):
		return {}



	data = json.loads(req.data)
	req.filedata = data['filedata']
	req.role = data['doctype']
	req.name = data['name']
	req.filename = "{}_{}.jpg".format(req.role, frappe.utils.now())

	# try:
	
	uploaded = upload(req.role,req.name,1)

	response["code"] = 200
	response["message"] = "Success"
	response["data"] = uploaded

	# frappe.db.commit()


	# except Exception as e:
	# 	response["code"] = 400
	# 	response["message"] = e.message
	# 	response["data"] = ""
	# except UnboundLocalError as e:
	# 	response["code"] = 401
	# 	response["message"] = e.message
	# 	response["data"] = ""

	return response

#================================================================REPORTING=============================

@frappe.whitelist(allow_guest=False)
def get_sales_report(interval=0, tipe=''):
	sales_partner = frappe.get_value("User Permission", {"user": frappe.session.user, "allow": "Sales Partner"}, "for_value")
	sales_manager = frappe.get_value("Has Role", {"parent": frappe.session.user, "role": "Sales Manager"}, "role")

	data = dict()
	week = int(interval) * 7
	month = int(interval) * 4
	year = int(interval) * 6
	
	if sales_manager:
		daily = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, DATE_FORMAT(daily.day, '%e %b') AS X FROM (SELECT DATE(NOW()) - INTERVAL (0 + {}) DAY AS day UNION ALL SELECT DATE(NOW()) - INTERVAL (1 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (2 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (3 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (4 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (5 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (6 + {}) DAY) daily LEFT JOIN (SELECT SUM(si.net_total) AS total, si.posting_date FROM `tabSales Invoice` si WHERE docstatus = 1 GROUP BY si.posting_date) sales ON sales.posting_date = daily.day;".format(week, week, week, week, week, week, week),as_dict=1)
		weekly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, weekly.week AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (0 + {}) WEEK, '%Y Week %u') AS week UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) WEEK, '%Y Week %u')) weekly LEFT JOIN (SELECT SUM(si.net_total) AS total, DATE_FORMAT(si.posting_date, '%Y Week %u') AS week FROM `tabSales Invoice` si WHERE docstatus = 1 GROUP BY (week)) sales ON sales.week = weekly.week;".format(month, month, month, month),as_dict=1)
		monthly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, monthly.month AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (0 + {}) MONTH, '%b-%y') AS month UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (5 + {}) MONTH, '%b-%y')) monthly LEFT JOIN (SELECT SUM(si.net_total) AS total, DATE_FORMAT(si.posting_date, '%b-%y') AS month FROM `tabSales Invoice` si WHERE docstatus = 1 GROUP BY (month)) sales ON sales.month = monthly.month;".format(year, year, year, year, year, year),as_dict=1)
	else:
		daily = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, DATE_FORMAT(daily.day, '%e %b') AS X FROM (SELECT DATE(NOW()) - INTERVAL (0 + {}) DAY AS day UNION ALL SELECT DATE(NOW()) - INTERVAL (1 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (2 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (3 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (4 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (5 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (6 + {}) DAY) daily LEFT JOIN (SELECT SUM(si.net_total) AS total, si.posting_date FROM `tabSales Invoice` si WHERE si.sales_partner = '{}' AND docstatus = 1 GROUP BY si.posting_date) sales ON sales.posting_date = daily.day;".format(week, week, week, week, week, week, week, sales_partner),as_dict=1)
		weekly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, weekly.week AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (0 + {}) WEEK, '%Y Week %u') AS week UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) WEEK, '%Y Week %u')) weekly LEFT JOIN (SELECT SUM(si.net_total) AS total, DATE_FORMAT(si.posting_date, '%Y Week %u') AS week FROM `tabSales Invoice` si WHERE si.sales_partner = '{}' AND docstatus = 1 GROUP BY (week)) sales ON sales.week = weekly.week;".format(month, month, month, month, sales_partner),as_dict=1)
		monthly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, monthly.month AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (0 + {}) MONTH, '%b-%y') AS month UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (5 + {}) MONTH, '%b-%y')) monthly LEFT JOIN (SELECT SUM(si.net_total) AS total, DATE_FORMAT(si.posting_date, '%b-%y') AS month FROM `tabSales Invoice` si WHERE si.sales_partner = '{}' AND docstatus = 1 GROUP BY (month)) sales ON sales.month = monthly.month;".format(year, year, year, year, year, year, sales_partner),as_dict=1)
	
	data["daily"] = daily
	data["weekly"] = weekly
	data["monthly"] = monthly

	return data


@frappe.whitelist(allow_guest=False)
def submit_sales_order(name):
	try:
		doc = frappe.get_doc("Sales Order", name)
		doc.docstatus = 1
		doc.status = "To Deliver and Bill"
		doc.save()
		return doc
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def cancel_sales_order(name):
	try:
		doc = frappe.get_doc("Sales Order", name)
		doc.docstatus = 2
		doc.status = "Cancelled"
		doc.save()
		return doc
	except:
		return error_format(sys.exc_info()[1])

# TOTAL SALES PER CUSTOMER
@frappe.whitelist(allow_guest=False)
def get_customer_sales(query='',last_day=0, sort='',page=0):
	seen = ""
	data = []
	
	filters = ["name", "customer_name"]

	for f in filters:
		data_filter = frappe.get_list("Customer", 
							fields="*", 
							filters = 
							{
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)

	for d in data:
		data_sales = frappe.db.sql("SELECT * FROM `tabSales Team` WHERE parent='{}'".format(d['name']),as_dict=1)
		d['sales_persons'] = data_sales
		
		fetchTotalSales  = frappe.db.sql("SELECT COALESCE(SUM(rounded_total * conversion_rate),0) FROM `tabSales Invoice` WHERE docstatus = 1 AND customer = '{}' AND posting_date BETWEEN DATE(NOW()) - INTERVAL {} DAY AND NOW()".format(d["name"],last_day))
		if (len(fetchTotalSales) > 0):
			d["last_total_sales"] = fetchTotalSales[0][0]

	return data

# ========================================================CUSTOMER====================================================
@frappe.whitelist(allow_guest=False)
def get_customer(query='',sort='',page=0):
	seen = ""
	data = []
	

	filters = ["name", "customer_name","territory"]

	for f in filters:
		data_filter = frappe.get_list("Customer", 
							fields="*", 
							filters = 
							{
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		for df in result_list:
			data_sales = frappe.db.sql("SELECT * FROM `tabSales Team` WHERE parent='{}'".format(df['name']),as_dict=1)
			df['sales_persons'] = data_sales
		seen = temp_seen
		data.extend(result_list)
	return data	


@frappe.whitelist(allow_guest=False)
def get_contact(customer=''):
	data = frappe.db.sql("SELECT * FROM `tabContact` WHERE name IN (SELECT parent FROM `tabDynamic Link` WHERE link_name ='{}' AND parenttype = '{}')".format(customer,'Contact'),as_dict=True)
	return data

# ========================================================SALES ORDER====================================================
standard_fields_of_sales_order = ["customer_section","column_break0","title","naming_series","customer","customer_name","order_type","column_break1","amended_from","company","transaction_date","delivery_date","po_no","po_date","tax_id","contact_info","customer_address","address_display","contact_person","contact_display","contact_mobile","contact_email","col_break46","shipping_address_name","shipping_address","customer_group","territory","currency_and_price_list","currency","conversion_rate","column_break2","selling_price_list","price_list_currency","plc_conversion_rate","ignore_pricing_rule","items_section","items","section_break_31","column_break_33a","base_total","base_net_total","column_break_33","total","net_total","total_net_weight","taxes_section","taxes_and_charges","column_break_38","shipping_rule","section_break_40","taxes","sec_tax_breakup","other_charges_calculation","section_break_43","base_total_taxes_and_charges","column_break_46","total_taxes_and_charges","section_break_48","apply_discount_on","base_discount_amount","column_break_50","additional_discount_percentage","discount_amount","totals","base_grand_total","base_rounding_adjustment","base_rounded_total","base_in_words","column_break3","grand_total","rounding_adjustment","rounded_total","in_words","advance_paid","packing_list","packed_items","payment_schedule_section","payment_terms_template","payment_schedule","terms_section_break","tc_name","terms","more_info","project","party_account_currency","column_break_77","source","campaign","printing_details","language","letter_head","column_break4","select_print_heading","group_same_items","section_break_78","status","delivery_status","per_delivered","column_break_81","per_billed","billing_status","sales_team_section_break","sales_partner","column_break7","commission_rate","total_commission","section_break1","sales_team","subscription_section","from_date","to_date","column_break_108","subscription"]
@frappe.whitelist(allow_guest=False)
def get_field_custom_sales_order():
	standard_fields = frappe.get_meta('Sales Order')

	raw_fields = standard_fields.fields
	fields = []
	for rf in raw_fields:
		if (rf.fieldname not in standard_fields_of_sales_order):
			if (rf.fieldtype == 'Data'):
				fields.append(rf.fieldname)


	return fields



@frappe.whitelist(allow_guest=False)
def get_sales_order_naming_series():
	so_meta = frappe.get_meta('Sales Order')

	
	raw_fields = so_meta.fields
	fields = []
	for rf in raw_fields:
		if (rf.fieldname == 'naming_series'):
			naming_series = rf.options.split('\n')
			data = []
			for ns in naming_series:
				dataNamingSeries = {'naming_series':ns}
				data.append(dataNamingSeries)

			return data		
			

	return []



@frappe.whitelist(allow_guest=False)
def get_sales_order(status='',query='',sort='',delivery_status='%',billing_status='%',page=0):
	seen = ""
	data = []
	
	statuses = status.split(',')
	filters = ["name", "customer_name"]

	for f in filters:
		data_filter = frappe.get_list("Sales Order", 
							fields="*", 
							filters = 
							{
								"status": ("IN", statuses),
								f: ("LIKE", "%{}%".format(query)),
								"delivery_status": ("LIKE",delivery_status),
								"billing_status": ("LIKE",billing_status)
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)

		
		temp_seen, result_list = distinct(seen,data_filter)
		for df in result_list:
			data_sales = frappe.db.sql("SELECT * FROM `tabSales Team` WHERE parent='{}'".format(df['name']),as_dict=1)
			df['sales_persons'] = data_sales
		seen = temp_seen
		data.extend(result_list)
	return data

@frappe.whitelist(allow_guest=False)
def validate_sales_order(items):
	return validate_warehouse(items)

@frappe.whitelist(allow_guest=False)
def update_stock_sales_order(so_name,customer,selling_price_list,price_list_currency,transaction_date,company, plc_conversion_rate, conversion_rate):
	data_sales_item = frappe.db.sql("SELECT * FROM `tabSales Order Item` WHERE parent='{}'".format(so_name),as_dict=1)
	for dsi in data_sales_item:
		args = {
			"item_code": dsi['item_code'],
			"warehouse": dsi['warehouse'],
			"company": company,
			"customer": customer,
			"conversion_rate": dsi['conversion_factor'],
			"selling_price_list": selling_price_list,
			"price_list_currency": price_list_currency,
			"plc_conversion_rate": plc_conversion_rate,
			"doctype": "Sales Order",
			"transaction_date": transaction_date,
			"conversion_rate": conversion_rate,
			"ignore_pricing_rule": 1
		}

		item_details = get_item_details(args)

		# frappe.db.sql("UPDATE `tabSales Order Item` SET actual_qty={}, project_qty={}, projected_qty={}, stock_qty={} WHERE name='{}'".format(item_details['actual_qty'],item_details['projected_qty'],item_details['projected_qty'],item_details['stock_qty'],dsi['name']))
		# frappe.db.commit()
		
	return data_sales_item


# ========================================================SALES INVOICE====================================================

@frappe.whitelist(allow_guest=False)
def get_sales_invoice(status='',query='',sort='',page=0):
	seen = ""
	data = []
	
	statuses = status.split(',')
	filters = ["name", "customer_name"]

	for f in filters:
		data_filter = frappe.get_list("Sales Invoice", 
							fields="*", 
							filters = 
							{
								"status": ("IN", statuses),
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		for df in result_list:
			data_sales = frappe.db.sql("SELECT * FROM `tabSales Team` WHERE parent='{}'".format(df['name']),as_dict=1)
			df['sales_persons'] = data_sales
		seen = temp_seen
		data.extend(result_list)
	return data

@frappe.whitelist(allow_guest=False)
def update_address(billing, shipping):
	customer = get_user_customer()
	doc = frappe.get_doc("Customer", customer["data"]["customer"]["name"])

@frappe.whitelist(allow_guest=False)
def get_item(is_sales_item='1',is_stock_item='1',ref='',sort='',page='0'):
	seen = ""
	data = []

	filters = ["item_name", "item_code"]

	for f in filters:
		data_filter = frappe.get_list("Item", 
							fields="*", 
							filters = 
							{
								"has_variants": 0,
								"is_sales_item":is_sales_item,
								"is_stock_item":is_stock_item,
								f: ("LIKE", "%{}%".format(ref))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)

	for row in data:
		row['product_bundle_item'] = list("")
		if (row['is_stock_item'] == 0):
			fetchBundleItem = frappe.get_list("Product Bundle Item", 
							fields="*", 
							filters = 
							{
								"parent":row['item_code']
							},
							limit_page_length=1000000)
			data_bundle_item = list("")
			for bundleItem in fetchBundleItem:
				fetchBundleItemDetails = frappe.get_list("Item", 
							fields="item_name", 
							filters = 
							{
								"item_code":bundleItem['item_code']
							})
				bundleItem['item_name'] = ""
				if (len(fetchBundleItemDetails) > 0):
					bundleItem['item_name'] = fetchBundleItemDetails[0]['item_name']
				data_bundle_item.append(bundleItem)
			row['product_bundle_item'] = data_bundle_item
	return data

@frappe.whitelist(allow_guest=False)
def get_item_price(item_code,customer,default_price_list):

	from nextapp.defaults import get_default_warehouse, get_default_company
	company = get_default_company()
	warehouse = get_default_warehouse()
	args = {
		"item_code": item_code,
		"warehouse": warehouse,
		"company": company,
		"customer": customer,
		"conversion_rate": 1,
		"selling_price_list": default_price_list,
		"price_list_currency": "IDR",
		"plc_conversion_rate": 1,
		"doctype": "Sales Order",
		"transaction_date": frappe.utils.today(),
		"conversion_rate": 1,
		"ignore_pricing_rule": 0
	}
	return get_item_details(args)

@frappe.whitelist(allow_guest=False)
def get_item_by_keyword(item_from, keyword=""):
	seen = ""
	data = []

	filters = ["keyword"]

	for f in filters:
		word = keyword.split("\n")
		query = "AND (i.{} LIKE '%{}%'".format(f, word[0])
		for i in range(len(word) - 1):
			query += " OR i.{} LIKE '%{}%'".format(f, word[i+1])
		query += ")"

		data_filter = frappe.db.sql("""
			SELECT
				i.name,
				i.item_code,
				i.item_name,
				i.image,
				i.total_projected_qty,
				i.projected_quantity,
				i.is_stock_item
			FROM `tabItem` i
			JOIN `tabItem Price` ip
			ON i.item_code = ip.item_code
			WHERE i.item_code != '{}'
			AND i.has_variants = 0
			AND i.projected_quantity > 0
			AND i.disabled = 0
			AND i.is_sales_item = '1'
			AND i.is_stock_item = '1'
			AND i.hide = 0
			{}
			ORDER BY i.creation DESC
			LIMIT 6
		""".format(item_from, query, LIMIT_PAGE), as_dict=True)
		# data_filter = frappe.get_list("Item", 
		# 					fields="*",
		# 					filters = 
		# 					{
		# 						"has_variants": 0,
		# 						"is_new_product": is_new_product,
		# 						"item_group": ("LIKE", "%{}%".format(item_group)),
		# 						"brand": ("LIKE", "%{}%".format(brand)),
		# 						"is_sales_item":is_sales_item,
		# 						"is_stock_item":is_stock_item,
		# 						f: ("LIKE", "%{}%".format(ref))
		# 					},
		# 					order_by=sort,
		# 					limit_page_length=LIMIT_PAGE,
		# 					limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
	
	customer = frappe.get_doc("Customer", frappe.get_value("Customer", {"user": frappe.session.user}))
	for row in data:
		#fetch price

		#optimize field
		item_price_res = get_item_price(row['item_code'],customer.name,customer.default_price_list)
		pricing_rules = eval(str(item_price_res.pricing_rules)) or []
		if len(pricing_rules) > 0:
			row['item_price'] = {
				"price_list_rate": item_price_res.price_list_rate,
				"projected_qty": item_price_res.projected_qty,
				"item_name": item_price_res.item_name,
				"pricing_rule": pricing_rules[0],
				"margin_type": item_price_res.margin_type,
				"margin_rate_or_amount": item_price_res.margin_rate_or_amount
			}
		else:
			row['item_price'] = {
				"price_list_rate": item_price_res.price_list_rate,
				"projected_qty": item_price_res.projected_qty,
				"item_name": item_price_res.item_name,
				"pricing_rule": '',
				"margin_type": item_price_res.margin_type,
				"margin_rate_or_amount": item_price_res.margin_rate_or_amount
			}
		# if row['item_price'].get("projected_qty", None):
		# 	row['total_projected_qty'] = row['item_price']['projected_qty']
		# else:
		# 	row['total_projected_qty'] = 0
		row['total_projected_qty'] = row['projected_quantity']
		row['product_bundle_item'] = list("")
		if (row['is_stock_item'] == 0):
			fetchBundleItem = frappe.get_list("Product Bundle Item", 
							fields="*", 
							filters = 
							{
								"parent":row['item_code']
							},
							limit_page_length=1000000)
			data_bundle_item = list("")
			for bundleItem in fetchBundleItem:
				fetchBundleItemDetails = frappe.get_list("Item", 
							fields="item_name", 
							filters = 
							{
								"item_code":bundleItem['item_code']
							})
				bundleItem['item_name'] = ""
				if (len(fetchBundleItemDetails) > 0):
					bundleItem['item_name'] = fetchBundleItemDetails[0]['item_name']
				data_bundle_item.append(bundleItem)
			row['product_bundle_item'] = data_bundle_item

	return success_format(data)

@frappe.whitelist(allow_guest=False)
def get_item_with_price(customer,is_sales_item='1',is_stock_item='1',ref='',page=0,item_group='',brand='',is_new_product='',sort_by='latest',show_empty_product="0"):
	seen = ""
	data = []

	filters = ["item_name", "item_code", "keyword"]

	if sort_by == "price_low_high":
		sort_by = "ip.price_list_rate ASC"
	elif sort_by == "price_high_low":
		sort_by = "ip.price_list_rate DESC"
	elif sort_by == "popularity":
		sort_by = "i.product_page_order DESC, i.creation DESC"
	elif sort_by == "latest":
		sort_by = "i.creation DESC"

	customer_doc = frappe.get_doc("Customer", customer)

	if show_empty_product == "0":
		show_empty_product = "AND i.projected_quantity > 0"
	else:
		show_empty_product = ""

	for f in filters:
		word = ref.split(" ")
		query = "AND (i.{} LIKE '%{}%'".format(f, word[0])
		for i in range(len(word) - 1):
			query += " AND i.{} LIKE '%{}%'".format(f, word[i+1])
		query += ")"

		data_filter = frappe.db.sql("""
			SELECT
				i.name,
				i.item_code,
				i.item_name,
				i.image,
				i.total_projected_qty,
				i.projected_quantity,
				i.is_stock_item
			FROM `tabItem` i
			JOIN `tabItem Price` ip
			ON i.item_code = ip.item_code
			WHERE i.has_variants = 0
			{}
			AND i.disabled = 0
			AND i.is_new_product LIKE '%{}%'
			AND i.item_group LIKE '%{}'
			AND i.brand LIKE '%{}'
			AND i.is_sales_item = '{}'
			AND i.is_stock_item = '{}'
			{}
			AND i.hide = 0
			AND ip.price_list = '{}'
			ORDER BY {} 
			LIMIT {}
			OFFSET {}
		""".format(show_empty_product, is_new_product, item_group, brand, is_sales_item, is_stock_item, query, customer_doc.default_price_list, sort_by, LIMIT_PAGE, page), as_dict=True)
		# return """SELECT i.name, i.item_code, i.item_name, i.image, i.total_projected_qty, i.projected_quantity, i.is_stock_item FROM `tabItem` i JOIN `tabItem Price` ip ON i.item_code = ip.item_code WHERE i.has_variants = 0 {} AND i.disabled = 0 AND i.is_new_product LIKE '%{}%' AND i.item_group LIKE '%{}' AND i.brand LIKE '%{}' AND i.is_sales_item = '{}' AND i.is_stock_item = '{}' {} AND i.hide = 0 AND ip.price_list = '{}' ORDER BY {} LIMIT {} OFFSET {}""".format(show_empty_product, is_new_product, item_group, brand, is_sales_item, is_stock_item, query, customer_doc.default_price_list, sort_by, LIMIT_PAGE, page)
		
		# data_filter = frappe.get_list("Item", 
		# 					fields="*",
		# 					filters = 
		# 					{
		# 						"has_variants": 0,
		# 						"is_new_product": is_new_product,
		# 						"item_group": ("LIKE", "%{}%".format(item_group)),
		# 						"brand": ("LIKE", "%{}%".format(brand)),
		# 						"is_sales_item":is_sales_item,
		# 						"is_stock_item":is_stock_item,
		# 						f: ("LIKE", "%{}%".format(ref))
		# 					},
		# 					order_by=sort,
		# 					limit_page_length=LIMIT_PAGE,
		# 					limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
		
	for row in data:
		#fetch price

		#optimize field
		item_price_res = get_item_price(row['item_code'],customer,customer_doc.default_price_list)
		pricing_rules = eval(str(item_price_res.pricing_rules)) or []
		if len(pricing_rules) > 0:
			row['item_price'] = {
				"price_list_rate": item_price_res.price_list_rate,
				"projected_qty": item_price_res.projected_qty,
				"item_name": item_price_res.item_name,
				"pricing_rule": pricing_rules[0],
				"margin_type": item_price_res.margin_type,
				"margin_rate_or_amount": item_price_res.margin_rate_or_amount
			}
		else:
			row['item_price'] = {
				"price_list_rate": item_price_res.price_list_rate,
				"projected_qty": item_price_res.projected_qty,
				"item_name": item_price_res.item_name,
				"pricing_rule": '',
				"margin_type": item_price_res.margin_type,
				"margin_rate_or_amount": item_price_res.margin_rate_or_amount
			}
		# if row['item_price'].get("projected_qty", None):
		# 	row['total_projected_qty'] = row['item_price']['projected_qty']
		# else:
		# 	row['total_projected_qty'] = 0
		row['total_projected_qty'] = row['projected_quantity']
		row['product_bundle_item'] = list("")
		if (row['is_stock_item'] == 0):
			fetchBundleItem = frappe.get_list("Product Bundle Item", 
							fields="*", 
							filters = 
							{
								"parent":row['item_code']
							},
							limit_page_length=1000000)
			data_bundle_item = list("")
			for bundleItem in fetchBundleItem:
				fetchBundleItemDetails = frappe.get_list("Item", 
							fields="item_name", 
							filters = 
							{
								"item_code":bundleItem['item_code']
							})
				bundleItem['item_name'] = ""
				if (len(fetchBundleItemDetails) > 0):
					bundleItem['item_name'] = fetchBundleItemDetails[0]['item_name']
				data_bundle_item.append(bundleItem)
			row['product_bundle_item'] = data_bundle_item
	# if sort_by == "price_low_high":
	# 	data.sort(key=take_item_price)
	# elif sort_by == "price_high_low":
	# 	data.sort(key=take_item_price, reverse=True)
	# elif sort_by == "popularity":
	# 	data.sort(key=take_item_total_sales, reverse=True)
	# elif sort_by == "latest":
	# 	data.sort(key=take_item_creation, reverse=True)
	return data
	#return data[int(page):int(page)+20]

@frappe.whitelist(allow_guest=False)
def test_get_item_with_price(is_sales_item='1',is_stock_item='1',ref='',page=0,item_group='',brand='',is_new_product='',sort_by='latest',show_empty_product="0"):
	seen = ""
	data = []
	customer = "SANDRO NJATAWIDJAJA"

	filters = ["item_name", "item_code"]

	if sort_by == "price_low_high":
		sort_by = "ip.price_list_rate ASC"
	elif sort_by == "price_high_low":
		sort_by = "ip.price_list_rate DESC"
	elif sort_by == "popularity":
		sort_by = "i.product_page_order DESC"
	elif sort_by == "latest":
		sort_by = "i.creation DESC"

	customer_doc = frappe.get_doc("Customer", customer)

	if show_empty_product == "0":
		show_empty_product = "AND i.projected_quantity > 0"
	else:
		show_empty_product = ""

	for f in filters:
		word = ref.split(" ")
		query = "AND (i.{} LIKE '%{}%'".format(f, word[0])
		for i in range(len(word) - 1):
			query += " AND i.{} LIKE '%{}%'".format(f, word[i+1])
		query += ")"

		data_filter = frappe.db.sql("""
			SELECT
				i.name,
				i.item_code,
				i.item_name,
				i.image,
				i.total_projected_qty,
				i.projected_quantity,
				i.is_stock_item
			FROM `tabItem` i
			JOIN `tabItem Price` ip
			ON i.item_code = ip.item_code
			WHERE i.has_variants = 0
			{}
			AND i.disabled = 0
			AND i.is_new_product LIKE '%{}%'
			AND i.item_group LIKE '%{}%'
			AND i.brand LIKE '%{}%'
			AND i.is_sales_item = '{}'
			AND i.is_stock_item = '{}'
			{}
			AND i.hide = 0
			AND ip.price_list = '{}'
			ORDER BY {} 
			LIMIT {}
			OFFSET {}
		""".format(show_empty_product, is_new_product, item_group, brand, is_sales_item, is_stock_item, query, customer_doc.default_price_list, sort_by, LIMIT_PAGE, page), as_dict=True)
		# data_filter = frappe.get_list("Item", 
		# 					fields="*",
		# 					filters = 
		# 					{
		# 						"has_variants": 0,
		# 						"is_new_product": is_new_product,
		# 						"item_group": ("LIKE", "%{}%".format(item_group)),
		# 						"brand": ("LIKE", "%{}%".format(brand)),
		# 						"is_sales_item":is_sales_item,
		# 						"is_stock_item":is_stock_item,
		# 						f: ("LIKE", "%{}%".format(ref))
		# 					},
		# 					order_by=sort,
		# 					limit_page_length=LIMIT_PAGE,
		# 					limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
		
	for row in data:
		#fetch price

		#optimize field
		item_price_res = get_item_price(row['item_code'],customer,customer_doc.default_price_list)

		row['item_price'] = {
			"price_list_rate": item_price_res.price_list_rate,
			"projected_qty": item_price_res.projected_qty,
			"item_name": item_price_res.item_name,
			"pricing_rule": item_price_res.pricing_rule,
			"margin_type": item_price_res.margin_type,
			"margin_rate_or_amount": item_price_res.margin_rate_or_amount
		}
		# if row['item_price'].get("projected_qty", None):
		# 	row['total_projected_qty'] = row['item_price']['projected_qty']
		# else:
		# 	row['total_projected_qty'] = 0
		row['total_projected_qty'] = row['projected_quantity']
		row['product_bundle_item'] = list("")
		if (row['is_stock_item'] == 0):
			fetchBundleItem = frappe.get_list("Product Bundle Item", 
							fields="*", 
							filters = 
							{
								"parent":row['item_code']
							},
							limit_page_length=1000000)
			data_bundle_item = list("")
			for bundleItem in fetchBundleItem:
				fetchBundleItemDetails = frappe.get_list("Item", 
							fields="item_name", 
							filters = 
							{
								"item_code":bundleItem['item_code']
							})
				bundleItem['item_name'] = ""
				if (len(fetchBundleItemDetails) > 0):
					bundleItem['item_name'] = fetchBundleItemDetails[0]['item_name']
				data_bundle_item.append(bundleItem)
			row['product_bundle_item'] = data_bundle_item
	# if sort_by == "price_low_high":
	# 	data.sort(key=take_item_price)
	# elif sort_by == "price_high_low":
	# 	data.sort(key=take_item_price, reverse=True)
	# elif sort_by == "popularity":
	# 	data.sort(key=take_item_total_sales, reverse=True)
	# elif sort_by == "latest":
	# 	data.sort(key=take_item_creation, reverse=True)
	return data
	#return data[int(page):int(page)+20]

def take_item_price(elem):
    return elem["item_price"]["price_list_rate"]

def take_item_creation(elem):
    return elem["creation"]

def take_item_total_sales(elem):
    return elem["total_sales"]

@frappe.whitelist(allow_guest=False)
def test_array():
	return {"message": []}

# ========================================================OFFER====================================================

@frappe.whitelist(allow_guest=False)
def get_lead(status='',query='',sort='',page=0):
	data = dict()
	
	#lead
	statuses = status.split(',')
	filters = ['name','company_name','lead_name','email_id']

	seen_leads = ""
	data['leads'] = []
	for f in filters:
		data_filter = frappe.get_list("Lead", 
							fields="*", 
							filters = 
							{
								"status": ("IN", statuses),
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen_leads, result_list = distinct(seen_leads,data_filter)
		seen_leads = temp_seen_leads
		data['leads'].extend(result_list)
	

	#quotation
	if 'Quotation' in statuses:
		quotation_statuses = ['Submitted', 'Open']
	elif 'Converted' in statuses:
		quotation_statuses = ['Ordered']
	else:
		quotation_statuses = []


	data['quotations'] = []
	if len(quotation_statuses) > 0:
		filters = ['name','customer_name','contact_email']

		seen_quotations = ""
		for f in filters:
			data_filter = frappe.get_list("Quotation", 
								fields="*", 
								filters = 
								{
									"quotation_to": "Customer",
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			temp_seen_quotations, result_list = distinct(seen_quotations,data_filter)
			seen_quotations = temp_seen_quotations
			data['quotations'].extend(result_list)


	#opportunity
	data['opportunities'] = []
	if 'Opportunity' in statuses:
		opportunity_statuses = ['Open']
		filters = ['name','customer_name','contact_email']

		seen_opportunities = ""
		for f in filters:
			data_filter = frappe.get_list("Opportunity", 
								fields="*", 
								filters = 
								{
									"status": ("IN", opportunity_statuses),
									"opportunity_from": "Customer",
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			temp_seen_opportunities, result_list = distinct(seen_opportunities,data_filter)
			seen_opportunities = temp_seen_opportunities
			data['opportunities'].extend(result_list)

	return data


@frappe.whitelist(allow_guest=False)
def get_quotation(status='',query='',sort='',page=0):
	quotation_statuses = status.split(',')
	filters = ['name','customer_name','contact_email']

	seen_quotations = ""
	for f in filters:
		data_filter = frappe.get_list("Quotation", 
							fields="*", 
							filters = 
							{
								"status": ("IN", quotation_statuses),
								"quotation_to": "Customer",
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen_quotations, result_list = distinct(seen_quotations,data_filter)
		seen_quotations = temp_seen_quotations
		data['quotations'].extend(result_list)

	return data


@frappe.whitelist(allow_guest=False)
def get_opportunity(status='',query='',sort='',page=0):
	opportunity_statuses = status.split(',')
	filters = ['name','customer_name','contact_email']

	seen_opportunities = ""
	for f in filters:
		data_filter = frappe.get_list("Opportunity", 
							fields="*", 
							filters = 
							{
								"status": ("IN", opportunity_statuses),
								"opportunity_from": "Customer",
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen_opportunities, result_list = distinct(seen_opportunities,data_filter)
		seen_opportunities = temp_seen_opportunities
		data['opportunities'].extend(result_list)

	return data

@frappe.whitelist(allow_guest=False)
def get_lead_item(lead_no=''):
	
	fetch_opportunity = frappe.get_list("Opportunity", 
							fields="*", 
							filters = 
							{
								"party_name": lead_no
							},
							limit_page_length=1000)
	fetch_quotation = frappe.get_list("Quotation", 
							fields="*", 
							filters = 
							{
								"party_name": lead_no
							},
							limit_page_length=1000)
	data = dict()
	data['opportunity'] = fetch_opportunity
	data['quotation'] = fetch_quotation
	return data


@frappe.whitelist(allow_guest=False)
def get_user():
	data = frappe.get_list("User", 
				fields="*",
				limit_page_length=1000)
	return data

@frappe.whitelist(allow_guest=False)
def get_user_customer():
	try:
		email = frappe.session.user
		user_doc = frappe.get_doc("User",email)
		user_dict = user_doc.as_dict(convert_dates_to_str=True)
		user_dict['frappe_userid'] = user_doc.social_logins[0].userid
		for role in user_doc.roles:
			if role.role == "Customer":
				customer = frappe.get_list("Customer",fields="*",filters={"user":email})
				if len(customer) > 0:
					address = frappe.db.sql("""SELECT * FROM `tabAddress` WHERE name IN (SELECT parent FROM `tabDynamic Link` WHERE link_name = "{}")""".format(customer[0]["name"]), as_dict=True)
					order_count = frappe.get_list("Sales Order", fields="*", filters={"customer":customer[0]["name"], "status": "Completed"})
					if len(address) > 0:
						return success_format({'user':user_dict, 'customer':customer[0], 'address': address, 'order_count': len(order_count)})
					else:
						return success_format({'user':user_dict, 'customer':customer[0]})
				else:
					return success_format({'user':user_dict})
		return error_format(["User is not Customer"])
	except:
		return error_format(sys.exc_info()[1])


# ========================================================WAREHOUSE====================================================
@frappe.whitelist(allow_guest=False)
def check_item(item_code='',query=""):

	data = dict()
	data_price_lists = frappe.get_list("Price List",
										fields="*",
										filters={
											"selling":1,
											"enabled":1
										})
	data_prices = []
	for data_price_list in data_price_lists:
		data_price = frappe.db.sql("SELECT price_list,price_list_rate FROM `tabItem Price` WHERE item_code = %(item_code)s AND price_list = %(price_list)s",{"item_code":item_code,"price_list":data_price_list["name"]},as_dict=True)
		# data_price = frappe.get_list("Item Price",
		# 								fields="price_list,price_list_rate",
		# 								filters={
		# 									"item_code":item_code,
		# 									"price_list":data_price_list["name"]
		# 								},
		# 								limit_page_length=100000)
		if (len(data_price) > 0):
			data_prices.append(data_price[0])
	data["item_price_list_rate"] = data_prices

	data_warehouses = frappe.get_list("Warehouse",
										fields="*",
										filters={
											"warehouse_name": ("LIKE","%{}%".format(query)),
											"is_group":0
										},
										order_by="modified DESC",
										limit_page_length=1000000
										)
	data_stocks = []
	for data_warehouse in data_warehouses:
		data_stock = frappe.get_list("Bin",
										fields="warehouse,actual_qty,projected_qty,reserved_qty",
										filters={
											"item_code":item_code,
											"warehouse": data_warehouse["name"]
										})
		if (len(data_stock) > 0):
			data_stocks.append(data_stock[0])
	data["warehouse_stocks"] = data_stocks
	return data

@frappe.whitelist(allow_guest=False)
def get_warehouse(company='',query='',sort='',page=0):
	return frappe.get_list("Warehouse", 
							fields="*", 
							filters = 
							{
								"is_group":0,
								"company":company,
								"name": ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)

@frappe.whitelist(allow_guest=False)
def set_address_customer():
	try:
		post = json.loads(frappe.request.data)
		customer = frappe.get_value("Customer", {"user": frappe.session.user}, "name")
		links=[{"link_doctype":"Customer", "link_name":customer}]
		doc = frappe.get_doc({
			"doctype": "Address",
			"address_type": post["address_type"],
			"address_title": customer,
			"address_line1": post["address_label"],
			"address_line2": post["address_line1"],
			"city": post["city"],
			"state": post["state"],
			"country": post["country"],
			"pincode": post["postal_code"],
			"phone": post.get("phone", None),
			"links": links
		})
		doc.insert(ignore_permissions=True)
		# frappe.db.commit()
		return success_format(doc)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def update_address_customer():
	try:
		post = json.loads(frappe.request.data)
		tax_id = frappe.get_value("Customer", {"user": frappe.session.user}, "tax_id")
		customer = frappe.get_value("Customer", {"user": frappe.session.user}, "name")
		doc = frappe.get_doc("Address", post["address_name"])
		if doc.is_primary_address == 1 and tax_id != "00.000.000.0-000.000":
			frappe.throw("Tidak dapat mengubah alamat penagihan")
		doc.address_line1 = post["address_line1"]
		doc.address_line2 = post["address_label"]
		doc.city = post["city"]
		doc.state = post["state"]
		doc.country = post["country"]
		doc.pincode = post["postal_code"]
		doc.phone = post.get("phone", None)
		doc.save(ignore_permissions=True)
		# frappe.db.commit()
		return success_format(doc)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def delete_address_customer(address_name):
	try:
		doc = frappe.get_doc("Address", address_name)
		doc.hide = 1
		doc.save(ignore_permissions=True)
		# frappe.db.commit()
		return success_format("Delete "+ address_name +" Success")
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def update_prefered_address(address_name, address_type):
	try:
		tax_id = frappe.get_value("Customer", {"user": frappe.session.user}, "tax_id")
		customer = frappe.get_value("Customer", {"user": frappe.session.user}, "name")
		address = frappe.db.sql("""SELECT * FROM `tabAddress` WHERE name IN (SELECT parent FROM `tabDynamic Link` WHERE link_name = "{}")""".format(customer), as_dict=True)
		for row in address:
			doc = frappe.get_doc("Address", row["name"])
			if doc.name == address_name:
				if address_type == "Billing":
					if tax_id != "00.000.000.0-000.000":
						frappe.throw("Cannot change preffered address please contact administrator")
					doc.is_primary_address = 1
				elif address_type == "Shipping":
					doc.is_shipping_address = 1
				elif address_type == "Dropship":
					doc.is_dropship_address = 1
			else:
				if address_type == "Billing":
					if tax_id != "00.000.000.0-000.000":
						frappe.throw("Cannot change preffered address please contact administrator")
					doc.is_primary_address = 0
				elif address_type == "Shipping":
					doc.is_shipping_address = 0
				elif address_type == "Dropship":
					doc.is_dropship_address = 0
			doc.save(ignore_permissions=True)
		# frappe.db.commit()
		return success_format(address)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_item(is_sales_item='1',is_stock_item='1',ref='',sort='',page='0'):
	seen = ""
	data = []

	filters = ["item_name", "item_code"]

	for f in filters:
		data_filter = frappe.get_list("Item", 
							fields="*", 
							filters = 
							{
								"has_variants": 0,
								"is_sales_item":is_sales_item,
								"is_stock_item":is_stock_item,
								f: ("LIKE", "%{}%".format(ref))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)

	for row in data:
		row['product_bundle_item'] = list("")
		if (row['is_stock_item'] == 0):
			fetchBundleItem = frappe.get_list("Product Bundle Item", 
							fields="*", 
							filters = 
							{
								"parent":row['item_code']
							},
							limit_page_length=1000000)
			data_bundle_item = list("")
			for bundleItem in fetchBundleItem:
				fetchBundleItemDetails = frappe.get_list("Item", 
							fields="item_name", 
							filters = 
							{
								"item_code":bundleItem['item_code']
							})
				bundleItem['item_name'] = ""
				if (len(fetchBundleItemDetails) > 0):
					bundleItem['item_name'] = fetchBundleItemDetails[0]['item_name']
				data_bundle_item.append(bundleItem)
			row['product_bundle_item'] = data_bundle_item
	return data