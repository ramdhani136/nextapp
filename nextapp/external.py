from __future__ import unicode_literals
import frappe
import json
import hashlib
import time
from frappe.utils.file_manager import *
from nextapp.base import validate_method
from frappe.utils import get_fullname, get_request_session
from frappe import utils
import sys
from api_integration.validation import *
from datetime import datetime

# ERPNEXT
from erpnext.stock.get_item_details import get_item_details

# CUSTOM METHOD
from nextapp.app.helper import *
from api_integration.validation import *
from api_integration.validation import * 
from api_integration.validation import *

LIMIT_PAGE = 20
API_VERSION = 1.9

def validate_token(token):
	check = frappe.get_all("Access Token",filters={"token":token})
	return len(check) > 0

@frappe.whitelist(allow_guest=True)
def get_item(token,is_sales_item='1',is_stock_item='1',ref='',sort='',page='0', last_modified=''):

	if (validate_token(token)):

		seen = ""
		data = []

		filters = ["item_name", "item_code"]

		if last_modified == '':
			last_modified = datetime(1900, 1, 1, 1, 1, 1, 0)

		for f in filters:
			data_filter = frappe.get_all("Item", 
								fields="name, item_name, item_code, description, modified", 
								filters = 
								{
									"has_variants": 0,
									"is_sales_item":is_sales_item,
									"is_stock_item":is_stock_item,
									f: ("LIKE", "%{}%".format(ref)),
									"modified": (">=", last_modified)
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=int(page) * LIMIT_PAGE)
			temp_seen, result_list = distinct(seen,data_filter)
			seen = temp_seen 
			data.extend(result_list)

		# response = []
		# for row in data:
		# 	if get_actual_qty(token, row["item_code"]) > 0:
		# 		response.append(row)
				
		# for row in data:
		# 	row['product_bundle_item'] = list("")
		# 	if (row['is_stock_item'] == 0):
		# 		fetchBundleItem = frappe.get_all("Product Bundle Item", 
		# 						fields="*", 
		# 						filters = 
		# 						{
		# 							"parent":row['item_code']
		# 						},
		# 						limit_page_length=1000000)
		# 		data_bundle_item = list("")
		# 		for bundleItem in fetchBundleItem:
		# 			fetchBundleItemDetails = frappe.get_all("Item", 
		# 						fields="item_name", 
		# 						filters = 
		# 						{
		# 							"item_code":bundleItem['item_code']
		# 						})
		# 			bundleItem['item_name'] = ""
		# 			if (len(fetchBundleItemDetails) > 0):
		# 				bundleItem['item_name'] = fetchBundleItemDetails[0]['item_name']
		# 			data_bundle_item.append(bundleItem)
		# 		row['product_bundle_item'] = data_bundle_item
		return success_format(data)
	else:
		return error_format("Token is not valid")


@frappe.whitelist(allow_guest=True)
def get_item_detail(token, item_code):
	from nextapp.defaults import get_default_warehouse, get_default_company
	company = get_default_company()
	if validate_token(token):
		customer, default_warehouse, default_price_list = frappe.get_value("Access Token",{"token":token},["customer","default_warehouse","default_price_list"])
		args = {
			"item_code": item_code,
			"warehouse": default_warehouse,
			"company": company,
			"customer": customer,
			"conversion_rate": 1,
			"currency":"IDR",
			"price_list": default_price_list,
			"price_list_currency": "IDR",
			"plc_conversion_rate": 1,
			"doctype": "Sales Order",
			"transaction_date": frappe.utils.today(),
			"ignore_pricing_rule": 0,
			"is_subcontracted":"No"
		}
		data = get_item_details(args)
		return success_format({"item_code":data['item_code'],"projected_qty":data['projected_qty'],"item_price":data["price_list_rate"],"item_name":data["item_name"],"description":data["description"]})
	else:
		return error_format("Token is invalid")


def get_actual_qty(token, item_code):
	if validate_token(token):
		from nextapp.defaults import get_default_warehouse, get_default_company
		company = get_default_company()
		customer, default_warehouse, default_price_list = frappe.get_value("Access Token",{"token":token},["customer","default_warehouse","default_price_list"])
		args = {
			"item_code": item_code,
			"warehouse": default_warehouse,
			"company":company,
			"customer": customer,
			"conversion_rate": 1,
			"currency":"IDR",
			"price_list": default_price_list,
			"price_list_currency": "IDR",
			"plc_conversion_rate": 1,
			"doctype": "Sales Order",
			"transaction_date": frappe.utils.today(),
			"ignore_pricing_rule": 0,
			"is_subcontracted":"No"
		}
		data = get_item_details(args)
		return data["actual_qty"]