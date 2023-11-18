from __future__ import unicode_literals
import frappe
import json
import hashlib
import time
from nextapp.file_manager import *
import operator
from nextapp.base import validate_method
from frappe import _
from frappe.utils import get_fullname
from frappe.auth import check_password 
from api_integration.validation import *
from datetime import date
from frappe.utils import get_request_session
import datetime
import random
import string

# CUSTOM METHOD
from nextapp.app.helper import *
from api_integration.validation import *
from api_integration.validation import *
from nextapp.nextsales import *



def random_string(stringLength=10):
	"""Generate a random string of fixed length """
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(stringLength))



LIMIT_PAGE = 20
API_VERSION = 1.5


@frappe.whitelist(allow_guest=True)
def me():
	try:
		me = frappe.session
		return me
	except:
		return error_format(sys.exc_info()[1])


@frappe.whitelist(allow_guest=True)
def ping():
	return "pong"

@frappe.whitelist(allow_guest=True)
def sales_force_validate():
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
def get_metadata(employee='%',company='',approver='%',is_sales="0",is_employee="0"):
	# MICH: (5/3/2021) 
	# user yang sudah disabled diharapkan keluar 
	enabled_user = frappe.get_value("User", frappe.session.user, "enabled")
	if enabled_user == 0:
		frappe.throw("User has been disabled")

	data = dict()

	if (is_employee == "1"):
		#daily net expense claim
		fetchExpenseClaim = frappe.get_list("Expense Claim",
										filters = {"employee": ("LIKE", employee)},
										fields = "SUM(total_claimed_amount) as net_expense_claim, posting_date",
										order_by = "posting_date DESC",
										group_by = "posting_date",
										limit_page_length = 7
									 )
		# fetchNetSales = frappe.db.sql("SELECT SUM(total_claimed_amount) as net_expense_claim, posting_date FROM `tabExpense Claim` WHERE employee LIKE '{}' AND company = '{}' AND approval_status='Approved' GROUP BY posting_date DESC LIMIT 7".format(employee,company),as_dict=1)
		data['daily_net_expense_claim'] = fetchExpenseClaim

		#leave application
		status = ["Open","Approved"]
		data['leave_application'] = dict()
		dataLA = data['leave_application']
		dataLA['count'] = dict()
		dataCount = dataLA['count']
		for stat in status:
			fetch = frappe.db.sql("SELECT COUNT(name) FROM `tabLeave Application` WHERE status='{}' AND employee LIKE '{}' AND company = '{}' ORDER BY modified".format(stat,employee,company),as_list=1)
			if (len(fetch) > 0):
				firstFetch = fetch[0]
				dataCount[stat] = firstFetch[0]

		#employee advance
		status = ['Draft','Unpaid','Claimed','Paid']
		data['employee_advance'] = dict()
		dataEA = data['employee_advance']
		dataEA['count'] = dict()
		dataCount = dataEA['count']
		for stat in status:
			fetch = frappe.db.sql("SELECT COUNT(name) FROM `tabEmployee Advance` WHERE status='{}' AND employee LIKE '{}' AND company = '{}' ORDER BY modified".format(stat,employee,company),as_list=1)
			if (len(fetch) > 0):
				firstFetch = fetch[0]
				dataCount[stat] = firstFetch[0]

		#expense claim
		status = ['Draft','Unpaid','Paid']
		data['expense_claim'] = dict()
		dataEC = data['expense_claim']
		dataEC['count'] = dict()
		dataCount = dataEC['count']
		for stat in status:
			fetch = frappe.db.sql("SELECT COUNT(name) FROM `tabExpense Claim` WHERE status='{}' AND employee LIKE '{}' AND company = '{}' ORDER BY modified".format(stat,employee,company),as_list=1)
			if (len(fetch) > 0):
				firstFetch = fetch[0]
				dataCount[stat] = firstFetch[0]

	else:
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

		#invoice
		status = ['Overdue','Unpaid','Paid']
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
		fetchNetSales = frappe.get_list("Sales Order",
										filters = {"status": ("IN", ["Open", "To Bill", "To Deliver", "To Deliver and Bill", "Completed"])},
										fields = ["SUM(grand_total) as net_sales", "transaction_date as posting_date"],
										order_by = "transaction_date DESC",
										group_by = "transaction_date",
										limit_page_length = 7
									 )
		data['daily_net_sales'] = fetchNetSales


		fetchPrintFormat = frappe.db.sql("SELECT name, doc_type FROM `tabPrint Format` WHERE disabled = 0",as_dict=1)

		data["print_format"] = fetchPrintFormat

	return data

@frappe.whitelist(allow_guest=False)
def get_sales_report(interval=0):
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
	elif sales_partner:
		daily = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, DATE_FORMAT(daily.day, '%e %b') AS X FROM (SELECT DATE(NOW()) - INTERVAL (0 + {}) DAY AS day UNION ALL SELECT DATE(NOW()) - INTERVAL (1 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (2 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (3 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (4 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (5 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (6 + {}) DAY) daily LEFT JOIN (SELECT SUM(si.net_total) AS total, si.posting_date FROM `tabSales Invoice` si WHERE si.sales_partner = '{}' AND docstatus = 1 GROUP BY si.posting_date) sales ON sales.posting_date = daily.day;".format(week, week, week, week, week, week, week, sales_partner),as_dict=1)
		weekly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, weekly.week AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (0 + {}) WEEK, '%Y Week %u') AS week UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) WEEK, '%Y Week %u')) weekly LEFT JOIN (SELECT SUM(si.net_total) AS total, DATE_FORMAT(si.posting_date, '%Y Week %u') AS week FROM `tabSales Invoice` si WHERE si.sales_partner = '{}' AND docstatus = 1 GROUP BY (week)) sales ON sales.week = weekly.week;".format(month, month, month, month, sales_partner),as_dict=1)
		monthly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, monthly.month AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (0 + {}) MONTH, '%b-%y') AS month UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (5 + {}) MONTH, '%b-%y')) monthly LEFT JOIN (SELECT SUM(si.net_total) AS total, DATE_FORMAT(si.posting_date, '%b-%y') AS month FROM `tabSales Invoice` si WHERE si.sales_partner = '{}' AND docstatus = 1 GROUP BY (month)) sales ON sales.month = monthly.month;".format(year, year, year, year, year, year, sales_partner),as_dict=1)
	else:
		daily = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, DATE_FORMAT(daily.day, '%e %b') AS X FROM (SELECT DATE(NOW()) - INTERVAL (0 + {}) DAY AS day UNION ALL SELECT DATE(NOW()) - INTERVAL (1 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (2 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (3 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (4 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (5 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (6 + {}) DAY) daily LEFT JOIN (SELECT SUM(si.net_total) AS total, si.posting_date FROM `tabSales Invoice` si WHERE docstatus = 1 GROUP BY si.posting_date) sales ON sales.posting_date = daily.day;".format(week, week, week, week, week, week, week),as_dict=1)
		weekly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, weekly.week AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (0 + {}) WEEK, '%Y Week %u') AS week UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) WEEK, '%Y Week %u')) weekly LEFT JOIN (SELECT SUM(si.net_total) AS total, DATE_FORMAT(si.posting_date, '%Y Week %u') AS week FROM `tabSales Invoice` si WHERE docstatus = 1 GROUP BY (week)) sales ON sales.week = weekly.week;".format(month, month, month, month),as_dict=1)
		monthly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, monthly.month AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (0 + {}) MONTH, '%b-%y') AS month UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) MONTH, '%b-%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (5 + {}) MONTH, '%b-%y')) monthly LEFT JOIN (SELECT SUM(si.net_total) AS total, DATE_FORMAT(si.posting_date, '%b-%y') AS month FROM `tabSales Invoice` si WHERE docstatus = 1 GROUP BY (month)) sales ON sales.month = monthly.month;".format(year, year, year, year, year, year),as_dict=1)

	data["daily"] = daily
	data["weekly"] = weekly
	data["monthly"] = monthly

	return data

@frappe.whitelist(allow_guest=False)
def get_sales_by_person():
	data = dict()
	data["sales_person"] = frappe.db.sql("SELECT st.sales_person AS 'Person Name', SUM(si.rounded_total) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent GROUP BY st.sales_person ORDER BY total_sales DESC", as_dict=True)
	data["sales_person_day"] = frappe.db.sql("SELECT st.sales_person AS 'Person Name', SUM(si.rounded_total) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE si.posting_date = CURDATE() GROUP BY st.sales_person ORDER BY total_sales DESC", as_dict=True)
	data["sales_person_month"] = frappe.db.sql("SELECT st.sales_person AS 'Person Name', SUM(si.rounded_total) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE DATE_FORMAT(si.posting_date, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m') GROUP BY st.sales_person ORDER BY total_sales DESC", as_dict=True)
	return data

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
		fetchTotalSales  = frappe.db.sql("SELECT SUM(rounded_total) FROM `tabSales Invoice` WHERE customer_name = '{}' AND posting_date BETWEEN DATE(NOW()) - INTERVAL {} DAY AND NOW()".format(d["customer_name"],last_day))
		d["total_sales"] = fetchTotalSales[0]

	return data


# LEAVE APPLICATION
@frappe.whitelist(allow_guest=False)
def get_leave_allocation(status='',query='',sort='',page=0):
	filters = ['name','leave_type','employee_name']
	n_filters = len(filters)
	generate_filters = ""
	for i in range(0,n_filters-1):
		generate_filters += "{} LIKE '%{}%' OR ".format(filters[i],query)
	generate_filters += "{} LIKE '%{}%' ".format(filters[n_filters-1],query)

	statuses = status.split(',')
	generate_status = "'" + "','".join(statuses) + "'"

	sortedby = 'modified'
	if (sort != ''):
		sortedby = sort

	data = frappe.db.sql("SELECT * FROM `tabLeave Allocation` WHERE docstatus = 1 AND status IN ({}) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(generate_status,generate_filters,sortedby,page),as_dict=1)

	return data

@frappe.whitelist(allow_guest=False)
def request_leave_application(employee='',company='',leave_type='', from_date='', to_date='', status='Open', half_day=0, half_day_date='',docstatus=0,leave_approver=None):
	error_message = []
	warning_message = []
	total_leave_days = 0

	#VALIDATION
	if not is_lwp(leave_type):
		result = validate_dates_acorss_allocation(employee, leave_type, from_date, to_date)
		if result != "":
			error_message.append(result)
		result = validate_back_dated_application(employee, leave_type, to_date)
		if result != "":
			error_message.append(result)
	result = validate_balance_leaves(employee, leave_type, from_date, to_date, half_day, half_day_date, status)
	if str(type(result)) == "<type 'int'>":
		total_leave_days = result
	else:
		error_message.append(result)

	result = validate_leave_overlap(total_leave_days,employee,from_date,to_date,half_day,half_day_date)
	if result != "":
		error_message.append(result)
	result = validate_max_days(total_leave_days, leave_type)
	if result != "":
		error_message.append(result)
	result = show_block_day_warning(employee,company,from_date,to_date)
	if result != "":
		warning_message.append(result)
	result = validate_block_days(employee,company,from_date, to_date,status)
	if result != "":
		error_message.append(result)
	result = validate_salary_processed_days(employee,leave_type, from_date,to_date)
	if result != "":
		error_message.append(result)
	result = validate_leave_approver(employee,leave_approver,docstatus)
	if result != "":
		error_message.append(result)
	result = validate_attendance(employee, from_date, to_date)
	if result != "":
		error_message.append(result)

	data = dict()
	data['warning_message'] = []
	data['error_message'] = []
	if (len(warning_message) > 0):
		data['result'] = 'success with some warning'
		data['warning_message'] = warning_message
	if (len(error_message) > 0):
		data['result'] = "not success"
		data['error_message'] = error_message
	else:
		data['result'] = "success"
	return data

@frappe.whitelist(allow_guest=False)
def get_leave_application(leave_approver='%',employee='',filter_requested='all',company='',status='',query='',sort='',page=0):
	seen = ""
	data = []

	statuses = status.split(',')
	filters = ['name','leave_type','employee_name']

	for f in filters:
		data_filter = []
		if filter_requested == 'me':
			data_filter = frappe.get_list("Leave Application",
								fields="*",
								filters =
								{
									"status": ("IN", statuses),
									"company": company,
									"employee": employee,
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
		elif filter_requested == 'other':
			data_filter = frappe.get_list("Leave Application",
								fields="*",
								filters =
								{
									"status": ("IN", statuses),
									"company": company,
									"leave_approver": ("LIKE", leave_approver),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
		else:
			data_filter_me = frappe.get_list("Leave Application",
								fields="*",
								filters =
								{
									"status": ("IN", statuses),
									"company": company,
									"employee": employee,
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			data_filter_other = frappe.get_list("Leave Application",
								fields="*",
								filters =
								{
									"status": ("IN", statuses),
									"company": company,
									"leave_approver": ("LIKE", leave_approver),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			data_filter.extend(data_filter_me)
			data_filter.extend(data_filter_other)

		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
	return data

@frappe.whitelist(allow_guest=False)
def get_leave_approver(employee=''):
	data = frappe.db.sql("SELECT * FROM `tabEmployee Leave Approver` WHERE parent = '{}' AND parentfield = 'leave_approvers'".format(employee),as_dict=1)

	leave_approvers = "'"
	for d in data:
		leave_approvers += d["leave_approver"] + "','"

	data = frappe.db.sql("SELECT full_name, name FROM `tabUser` WHERE name IN ({}')".format(leave_approvers),as_dict=1)

	return data

# EXPENSE

def validate_expense_approver(exp_approver):
	if exp_approver and "Expense Approver" not in frappe.get_roles(exp_approver):
		return "{0} ({1}) must have role 'Expense Approver'".format(get_fullname(exp_approver), exp_approver)
	return ""

def validate_expense_account(expense_claim_type, company):
	account = frappe.db.get_value("Expense Claim Account",
		{"parent": expense_claim_type, "company": company}, "default_account")
	if not account:
		return expense_claim_type
	return ""



@frappe.whitelist(allow_guest=False)
def request_expense_claim(exp_approver='', company='',expense_claim_type=''):
	error_message = []
	warning_message = []
	total_leave_days = 0

	result = validate_expense_approver(exp_approver)
	if result != "":
		error_message.append(result)
	ects = expense_claim_type.split(',')
	error_ects = []
	for ect in ects:
		result = validate_expense_account(ect,company)
		if result != "":
			error_ects.append(result)

	if len(error_ects) > 0:
		generated_error_ects = ",".join(error_ects)
		error_message.append("Please set default account in Expense Claim Type {0}".format(generated_error_ects))

	data = dict()
	data['warning_message'] = []
	data['error_message'] = []
	if (len(warning_message) > 0):
		data['result'] = 'success with some warning'
		data['warning_message'] = warning_message
	if (len(error_message) > 0):
		data['result'] = "not success"
		data['error_message'] = error_message
	else:
		data['result'] = "success"
	return data


@frappe.whitelist(allow_guest=False)
def get_expense_claim(exp_approver='%',filter_requested='all',employee='',company='',status='',approval_status='',query='',sort='',page=0):
	seen = ""
	data = []

	approval_statuses = approval_status.split(',')
	statuses = status.split(',')
	filters = ['name','employee_name']

	for f in filters:
		data_filter = []
		if filter_requested == 'me':
			data_filter = frappe.get_list("Expense Claim",
								fields="*",
								filters =
								{
									"status": ("IN", statuses),
									"company": company,
									"employee": employee,
									"approval_status": ("IN", approval_statuses),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
		elif filter_requested == 'other':
			data_filter = frappe.get_list("Expense Claim",
								fields="*",
								filters =
								{
									"status": ("IN", statuses),
									"company": company,
									"approval_status": ("IN", approval_statuses),
									"exp_approver": ("LIKE", exp_approver),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
		else:
			data_filter_me = frappe.get_list("Expense Claim",
								fields="*",
								filters =
								{
									"status": ("IN", statuses),
									"company": company,
									"employee": employee,
									"approval_status": ("IN", approval_statuses),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			data_filter_other = frappe.get_list("Expense Claim",
								fields="*",
								filters =
								{
									"status": ("IN", statuses),
									"company": company,
									"approval_status": ("IN", approval_statuses),
									"exp_approver": ("LIKE", exp_approver),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			data_filter.extend(data_filter_me)
			data_filter.extend(data_filter_other)

		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)


	return data


	# n_filters = len(filters)
	# generate_filters = ""
	# for i in range(0,n_filters-1):
	# 	generate_filters += "{} LIKE '%{}%' OR ".format(filters[i],query)
	# generate_filters += "{} LIKE '%{}%' ".format(filters[n_filters-1],query)

	# approval_statuses = approval_status.split(',')
	# generate_approval_status = "'" + "','".join(approval_statuses) + "'"
	# statuses = status.split(',')
	# generate_status = "'" + "','".join(statuses) + "'"

	# sortedby = 'modified'
	# if (sort != ''):
	# 	sortedby = sort

	# if filter_requested == 'me':
	# 	query = "SELECT * FROM `tabExpense Claim` WHERE employee LIKE '{}' AND company = '{}' AND (status IN ({}) AND approval_status IN ({})) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(employee,company,generate_status,generate_approval_status,generate_filters,sortedby,page)
	# elif filter_requested == 'other':
	# 	query = "SELECT * FROM `tabExpense Claim` WHERE exp_approver LIKE '{}' AND company = '{}' AND (status IN ({}) AND approval_status IN ({})) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(exp_approver,company,generate_status,generate_approval_status,generate_filters,sortedby,page)
	# elif filter_requested == 'all':
	# 	query = "SELECT * FROM `tabExpense Claim` WHERE (exp_approver LIKE '{}' OR employee LIKE '{}') AND company = '{}' AND (status IN ({}) AND approval_status IN ({})) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(exp_approver, employee,company,generate_status,generate_approval_status,generate_filters,sortedby,page)
	# data = frappe.db.sql(query,as_dict=1)

	# return data


@frappe.whitelist(allow_guest=True)
def attach_image_to_expense_claim():
	response = {}

	validate = validate_method(frappe.local.request.method,["POST"])
	if validate != True:
		return validate

	req = frappe.local.form_dict

	hash = hashlib.sha1()
	hash.update(str(time.time()).encode('utf-8'))
	hash_now = hash.hexdigest()[:10]
	req.filename = "attachment_{}.jpg".format(hash_now)




	data = json.loads(frappe.request.data.decode('utf-8'))
	req.filedata = data['filedata']
	req.expense_claim = data['expense_claim']

	try:

		from nextapp.file_manager import upload
		uploaded = upload("Expense Claim",req.expense_claim,1)

		response["code"] = 200
		response["message"] = "Success"
		response["data"] = uploaded

	except Exception as e:
		response["code"] = 400
		response["message"] = e.message
		response["data"] = ""
	except UnboundLocalError as e:
		response["code"] = 400
		response["message"] = e.message
		response["data"] = ""

	return response


@frappe.whitelist(allow_guest=False)
def get_expense_approver():
	user = frappe.session.user
	data = frappe.db.sql("SELECT parent FROM `tabHas Role` WHERE role ='Expense Approver'".format(user),as_dict=1)

	exp_approvers = "'"
	for d in data:
		exp_approvers += d["parent"] + "','"

	data = frappe.db.sql("SELECT full_name, name FROM `tabUser` WHERE name IN ({}')".format(exp_approvers),as_dict=1)

	return data

@frappe.whitelist(allow_guest=False)
def approve_expense_claim(approve='',is_paid='',name=''):
	status = 'Draft'
	approval_status = 'Draft'
	if approve == '1':
		approval_status = 'Approved'
		if is_paid == '1':
			status = 'Paid'
		else:
			status = 'Unpaid'
	else:
		approval_status = 'Rejected'
		status = 'Rejected'

	doc = frappe.get_doc("Expense Claim", name)
	doc.status = status
	doc.approval_status = approval_status
	doc.save()

	# result = frappe.db.sql("UPDATE `tabExpense Claim` SET status = '{}', docstatus=1, approval_status = '{}' WHERE name = '{}'".format(status, approval_status, name))
	# frappe.db.commit()
	return result

# EMPLOYEE ADVANCE
@frappe.whitelist(allow_guest=False)
def get_employee_advance(owner='%',employee='%', company='', status='',query='',sort='',page=0):
	seen = ""
	data = []

	statuses = status.split(',')
	filters = ['name','employee_name','purpose']

	for f in filters:
		data_filter = frappe.get_list("Employee Advance",
							fields="*",
							filters =
							{
								"status": ("IN", statuses),
								"company": company,
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
	return data

	# filters = ['name','employee_name','purpose']
	# n_filters = len(filters)
	# generate_filters = ""
	# for i in range(0,n_filters-1):
	# 	generate_filters += "{} LIKE '%{}%' OR ".format(filters[i],query)
	# generate_filters += "{} LIKE '%{}%' ".format(filters[n_filters-1],query)

	# statuses = status.split(',')
	# generate_status = "'" + "','".join(statuses) + "'"

	# sortedby = 'modified'
	# if (sort != ''):
	# 	sortedby = sort



	# data = frappe.db.sql("SELECT * FROM `tabEmployee Advance` WHERE (owner LIKE '{}' OR employee LIKE '{}') AND company='{}' AND status IN ({}) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(owner,employee,company,generate_status,generate_filters,sortedby,page),as_dict=1)

	# return data

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

# ========================================================SALES ORDER====================================================
@frappe.whitelist(allow_guest=False)
def get_sales_order(status='',query='',sort='',page=0):
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
def validate_sales_order(items):
	return validate_warehouse(items)

@frappe.whitelist(allow_guest=False)
def get_address(doctype,docname):
	address_name = frappe.get_value("Dynamic Link", {"link_doctype": doctype, "link_name": docname }, "parent")
	doc = frappe.get_doc("Address", address_name)
	return [doc]

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
								"lead": lead_no
							},
							limit_page_length=1000)
	fetch_quotation = frappe.get_list("Quotation",
							fields="*",
							filters =
							{
								"lead": lead_no
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
		data_price = frappe.db.sql("SELECT price_list,price_list_rate FROM `tabItem Price` WHERE item_code = '{}' AND price_list = '{}'".format(item_code,data_price_list["name"]),as_dict=True)
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
										order_by="modified",
										limit_page_length=1000000
										)
	data_stocks = []
	for data_warehouse in data_warehouses:
		data_stock = frappe.get_list("Bin",
										fields="warehouse,actual_qty,projected_qty",
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
def test_warehouse(company='',query='',sort='',page=0):
	return frappe.get_list("Warehouse",
							fields="name",
							filters =
							{
								"is_group":0,
								"company":company,
								"warehouse_name": ("LIKE", "%depo%")
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)



@frappe.whitelist(allow_guest=False)
def get_best_selling_product():
	try:
		user_id = get_user_id_by_session()
		customer_doc = frappe.get_doc("Customer",user_id)
		response = frappe.get_list("Item", fields="*", filters={"is_best_selling": 1, "disabled": 0, "hide": 0, "projected_quantity": (">", 0)}, order_by="item_name ASC")
		for row in response:
			if row["image"] == "" or row["image"] == None:
				row["image"] = "/files/no_image.jpeg"
			row["item_price"] = get_item_price(row["name"], user_id, customer_doc.default_price_list)
			row['total_projected_qty'] = row['projected_quantity']
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_new_product():
	try:
		user_id = get_user_id_by_session()
		customer_doc = frappe.get_doc("Customer",user_id)
		response = frappe.get_list("Item", fields="*", filters={"is_new_product": 1, "disabled": 0, "hide": 0, "projected_quantity": (">", 0)}, order_by="item_name ASC")
		for row in response:
			if row["image"] == "" or row["image"] == None:
				row["image"] = "/files/no_image.jpeg"
			row["item_price"] = get_item_price(row["name"], user_id, customer_doc.default_price_list)
			row['total_projected_qty'] = row['projected_quantity']
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_discount_product():
	try:
		user_id = get_user_id_by_session()
		customer_doc = frappe.get_doc("Customer",user_id)
		response = frappe.get_list("Item", fields="*", filters={"is_discount_product": 1, "disabled": 0, "hide": 0, "projected_quantity": (">", 0)}, order_by="item_name ASC")
		for row in response:
			if row["image"] == "" or row["image"] == None:
				row["image"] = "/files/no_image.jpeg"
			row["item_price"] = get_item_price(row["name"], user_id, customer_doc.default_price_list)
			row['total_projected_qty'] = row['projected_quantity']
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_brand_favorite():
	try:
		response = frappe.get_list("Brand", fields="brand_image, description", filters={"is_favorite": 1, "hide": 0}, limit_page_length=8)
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])



@frappe.whitelist(allow_guest=False)
def get_category_product(brand=""):
	try:
		response = frappe.db.sql("SELECT DISTINCT i.item_group AS name FROM `tabItem` i LEFT JOIN `tabItem Group` ig ON i.item_group = ig.name WHERE i.brand LIKE '%{}%' AND ig.hide = 0".format(brand),as_dict=True)
		# response = frappe.get_list("Item Group", fields="name", filters={"hide": 0}, order_by="name ASC")
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_brand():
	try:
		response = frappe.get_list("Brand", fields="name", filters={"hide": 0}, order_by="name ASC")
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_product():
	try:
		response = frappe.get_list("Item", fields="*", filters={"hide": 0})
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_detail_product(item):
	try:
		user_id = get_user_id_by_session()
		customer_doc = frappe.get_doc("Customer",user_id)
		response = frappe.get_list("Item", fields="*", filters={"name": item})
		if len(response) > 0:
			item_price = get_item_price(response[0]["name"], user_id, customer_doc.default_price_list)
			response[0]["file"] = frappe.get_list("File", fields="*", filters={"attached_to_doctype": "Item", "attached_to_name": response[0]["name"]})
			i = 0
			while i < len(response[0]["file"]):
				if response[0]["file"][i]["file_url"] == frappe.get_value("Item", item, "image"):
					tmp = response[0]["file"][0]["file_url"]
					response[0]["file"][0]["file_url"] = frappe.get_value("Item", item, "image")
					response[0]["file"][i]["file_url"] = tmp
				i += 1
			response[0]["standard_rate"] = item_price["price_list_rate"]
			response[0]["total_projected_qty"] = response[0]["projected_quantity"]
			response[0]["item_price"] = item_price
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_order(page=0, query=''):
	try:
		user_id = get_user_id_by_session()
		response = frappe.get_list("Sales Order", fields="*", filters={"customer": user_id, "name": ("LIKE", "%{}%".format(query))}, limit_page_length=LIMIT_PAGE, limit_start=page, order_by="name DESC")
		for res in response:
			sales_invoice_item = frappe.get_list("Sales Invoice Item", fields="*", filters={"sales_order": res["name"]})
			if len(sales_invoice_item) > 0:
				res['sales_invoice'] = frappe.get_list("Sales Invoice", fields="*", filters={"name":sales_invoice_item[0]["parent"]})
				res['status'] = _(res['status'])
		return success_format(response)
	except:
		return error_format(sys.exc_info()[1])
		
@frappe.whitelist(allow_guest=False)
def get_invoice(page=0, query=''):
	try:
		user_id = get_user_id_by_session()
		sales_invoice_item = frappe.get_list("Sales Invoice Item", fields="*", filters={"sales_order": res["name"]})
		if len(sales_invoice_item) > 0:
			sales_invoice = frappe.get_list("Sales Invoice", fields="*", filters={"name":sales_invoice_item[0]["parent"], "customer": user_id})
			return success_format(sales_invoice)
		else:
			return error_format("Sales Invoice not found")
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_order_detail(order):
	try:
		user_id = get_user_id_by_session()
		response = frappe.get_all("Sales Order", fields="*", filters={"name": order, "customer": user_id})
		if len(response) > 0:
			response[0]["item_list"] = frappe.get_all("Sales Order Item", fields="image, item_name, rate, qty, amount", filters={"parent": order})
			response[0]["delivery_note"] = frappe.db.sql("SELECT * FROM `tabDelivery Note` WHERE name IN (SELECT DISTINCT parent FROM `tabDelivery Note Item` WHERE against_sales_order = '{}')".format(order),as_dict=True)
			xendit_document = frappe.get_value(response[0]["xendit_payment_type"], {"external_id": order}, "name")
			if xendit_document:
				response[0]["xendit_document"] = frappe.get_doc(response[0]["xendit_payment_type"], xendit_document)
			else:
				response[0]["xendit_document"] = {}
			return success_format(response)
		else:
			return error_format("Order not found")
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def get_account():
	try:
		user_id = get_user_id_by_session()
		customer = frappe.get_list("Customer", fields="image", filters={"name": user_id})
		if len(customer) > 0:
			dynamic_link = frappe.get_list("Dynamic Link", fields="parent", filters={"link_name": user_id})
			if len(dynamic_link) > 0:
				address = frappe.get_list("Address", fields="email_id, phone, address_line1, pincode", filters={"name": dynamic_link[0]["parent"]})
				if len(address) > 0:
					response = dict()
					response["name"] = user_id
					response["email"] = frappe.session.user
					response["phone"] = address[0]["phone"]
					response["address"] = address[0]["address_line1"]
					response["zip_code"] = address[0]["pincode"]
					response["photo_path"] = customer[0]["image"]
					return success_format(response)
				else:
					return error_format("Address not found")
		else:
			return error_format("Customer not found")
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def upload_image_profile():
	try:
		response = {}
		req = frappe.local.form_dict
		if (req == None):
			return {}

		user_id = get_user_id_by_session()
		if (user_id == ''):
			response['code'] = 417
			response['message'] = 'Session user invalid'
			response['data'] = None
			return response
		req.filename = "profile_{}.jpg".format(user_id)

		data = json.loads(frappe.request.data.decode('utf-8'))
		req.filedata = data['filedata']
		req.role = data['role']
		req.name = data['name']

		# frappe.db.sql("""DELETE FROM `tabFile` WHERE attached_to_name="{}" AND attached_to_doctype="{}";""".format(req.name,req.role))
		# frappe.db.commit()

		from nextapp.file_manager import upload
		uploaded = upload(req.role,req.name,0)

		response["code"] = 200 
		response["message"] = "Success"
		response["data"] = uploaded

		doc_user = frappe.get_doc(req.role,req.name)
		doc_user.image = uploaded['file_url']
		doc_user.save(ignore_permissions=True)
		# frappe.db.commit()

		return success_format("SUKSES")
	except:
		return error_format(sys.exc_info())


@frappe.whitelist(allow_guest=False)
def change_password():
	if frappe.request.data is None:
		return "Forbidden"

	data = json.loads(frappe.request.data.decode('utf-8'))

	email = frappe.session.user
	data_user = frappe.db.sql("SELECT name FROM `tabUser` WHERE name='{}'".format(email),as_dict=True)

	if (len(data_user) > 0):
		try:
			check_password(data_user[0]['name'],data['old_pwd'])
		except frappe.AuthenticationError:
			return error_format('old password is incorrect')

		new_user = {
			"new_password":data['new_pwd']
		}

		doc = frappe.get_doc("User",data_user[0]['name'])
		doc.flags.ignore_permissions = True
		doc.update(new_user)
		doc.save()
		# frappe.db.commit()

		return success_format(doc)
	return error_format('not found')


@frappe.whitelist(allow_guest=True)
def set_account():
	try:
		frappe.db.begin()
		post = json.loads(frappe.request.data.decode('utf-8'))

		roles_to_apply=[{"role":"Customer"}]
		doc = frappe.get_doc({
			"doctype": "User",
			"email": post["email"],
			"first_name": post["full_name"],
			"send_welcome_email": 0,
			"new_password": post["password"],
			"send_password_update_notification": 0,
			"roles": roles_to_apply,
			"mobile_no": post["mobile_no"],
			"enabled": 0
		})
		doc.insert(ignore_permissions=True)

		doc_cust = frappe.get_doc({
			'doctype': 'Customer',
			'customer_name': post["store_name"],
			"customer_type": "Individual",
			'customer_group': 'All Customer Groups',
			'nama_pajak': post["full_name"],
			'address_title_billing': post["store_name"],
			'address_title_shipping': post["store_name"],
			'email_address_billing': post["email"],
			'phone_billing': post["mobile_no"],
			'phone_shipping': post["mobile_no"],
			'territory': "All Territories",
			'store_name': post["store_name"],
			'email': post["email"],
			'user': post["email"],
			'status': 'Draft',
			'tax_id': '00.000.000.0-000.000',
			'disabled': 1
		})
		doc_cust.insert(ignore_permissions=True)

		doc_contact = frappe.get_doc({
			'doctype': 'Contact',
			'first_name': post["full_name"],
			'phone': post["mobile_no"],
			'whatsapp': post["mobile_no"],
			'links': [{
				'link_name': doc_cust.name,
				'link_doctype': 'Customer'
			}]
		})
		doc_contact.insert(ignore_permissions=True)

		user_id = doc_cust.name
		req = frappe.local.form_dict
		response = {}
		hash = hashlib.sha1()
		hash.update(str(time.time()).encode('utf-8'))
		hash_now = hash.hexdigest()[:10]
		data = json.loads(frappe.request.data.decode('utf-8'))
		req.filename = "ktp_{}_{}.jpg".format(hash_now,user_id)
		req.filedata = data['filedata']
		req.name = user_id

		from nextapp.file_manager import upload
		sf = save_file(req.filename, req.filedata, "Customer", req.name, folder=None, decode=False, is_private=0, df=None)
		userDoc = frappe.get_doc("Customer", req.name)
		userDoc.profile_picture = sf.file_url
		userDoc.save(ignore_permissions=True)

		req = frappe.local.form_dict
		req.filename = "toko_{}_{}.jpg".format(hash_now,user_id)
		req.filedata = data['filedata2']
		req.name = user_id

		sf = save_file(req.filename, req.filedata, "Customer", req.name, folder=None, decode=False, is_private=0, df=None)
		userDoc = frappe.get_doc("Customer", req.name) 
		userDoc.profile_picture = sf.file_url
		userDoc.save(ignore_permissions=True)

		# frappe.db.commit()

		return success_format(doc_cust) 

	except:
		frappe.db.rollback()
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def verify_tax_id():
	tax_id = frappe.get_value("Customer", {"user": frappe.session.user}, "tax_id")
	if tax_id == "00.000.000.0-000.000":
		return success_format(True)
	else:
		return success_format(False)

@frappe.whitelist(allow_guest=False)
def get_user_id_by_session():
	return frappe.get_value("Customer", {"user": frappe.session.user}, "name")

@frappe.whitelist(allow_guest=True)
def get_city(city="", ref=""):
	try:
		response = {}
		if city == "":
			response = frappe.get_list("Territory", fields="*", filters={"is_group": 0, "hide": 0, "name": ("LIKE", "%{}%".format(ref))}, order_by="name ASC")
		else:
			response = frappe.get_list("Territory", fields="*", filters={"name": city, "hide": 0}, order_by="name ASC")
		for r in response:
			r["parent_territory"] = frappe.get_value("Territory", r["parent_territory"], "parent_territory")
		return success_format(response)
	except:
		return error_format(sys.exc_info())

@frappe.whitelist(allow_guest=True)
def test():
	return _("Completed")


@frappe.whitelist(allow_guest=True)
def reset_password(email):
	try:
		new_password = random_string()
		customer = frappe.get_value("Customer",{"user":email},["name","customer_name"])
		if customer:
			doc = frappe.get_doc({
				"doctype": "Reset Password",
				"user": email,
				"customer": customer[0],
				"customer_name": customer[1],
				"new_password": new_password
			})
			doc.insert(ignore_permissions=True)

			user_doc = frappe.get_doc("User",email)
			user_doc.flags.ignore_permissions = True
			user_doc.new_password = new_password
			user_doc.save()
			# frappe.db.commit()
			return success_format('Password baru telah dikirim ke Email Anda')
		else:
			return error_format('Email belum terdaftar')
	except:
		return error_format(sys.exc_info())

@frappe.whitelist(allow_guest=True)
def get_app_version():
	response = dict()
	response["android_minimum_version"] = frappe.get_single("App Version").android_minimum_version
	response["is_maintenance"] = frappe.get_single("App Version").is_maintenance
	return success_format(response)

@frappe.whitelist(allow_guest=True)
def get_tnc():
	return success_format(frappe.get_single("Next Sales Setting").term_and_condition)

@frappe.whitelist(allow_guest=True)
def is_active(email):
	return success_format(frappe.get_value("Customer", {"user": email}, "status"))


@frappe.whitelist(allow_guest=False)
def get_pusat_bantuan():
	try:
		pusat_bantuan = frappe.get_single("Next Sales Setting").pusat_bantuan
		return success_format(pusat_bantuan)
	except:
		return error_format(sys.exc_info())

@frappe.whitelist(allow_guest=False)
def get_pusat_bantuan():
	try:
		pusat_bantuan = frappe.get_single("Next Sales Setting").pusat_bantuan
		return success_format(pusat_bantuan)
	except:
		return error_format(sys.exc_info())
