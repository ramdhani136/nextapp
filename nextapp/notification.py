import frappe
import shlex
import subprocess
from frappe.utils import get_request_session
from api_integration.validation import *
from nextapp.constant import *

@frappe.whitelist(allow_guest=False)
def send_notification(user):
	try:
		docUser = frappe.get_doc("User", user)
		s = get_request_session()
		url = "https://fcm.googleapis.com/fcm/send"
		header = {"Authorization": "key={}".format(FCM),"Content-Type": "application/json"}
		content = {
			"to":"/topics/All",#.format(docUser.frappe_userid),
			"data": {
				"action": "SALES_ORDER",
				"content": ""
			}
		} 
		print(content)
		res = s.post(url=url,headers=header,data=json.dumps(content),verify=False)
		return res
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def notification_order_status(user, sales_order):
	try:
		docUser = frappe.get_doc("User", user)
		s = get_request_session()
		url = "https://fcm.googleapis.com/fcm/send"
		header = {"Authorization": "key={}".format(FCM),"Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(docUser.frappe_userid),
			"data": {
				"action": "SALES_ORDER",
				"sales_order": sales_order.name,
				"customer": sales_order.customer,
				"transaction_date": str(sales_order.transaction_date),
				"total": sales_order.total,
				"status": sales_order.status
			}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content),verify=False)
		return res
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def notification_delivery(user, deliver_note):
	try:
		docUser = frappe.get_doc("User", user)
		s = get_request_session()
		url = "https://fcm.googleapis.com/fcm/send"
		header = {"Authorization": "key={}".format(FCM),"Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(docUser.frappe_userid),
			"data": {
				"action": "DELIVER",
				"deliver_note": deliver_note.name,
				"customer": deliver_note.customer,
				"total": deliver_note.total,
				"status": deliver_note.workflow_state
			}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content),verify=False)
		return res
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def notification_all(name, title, body, image="", action="GLOBAL", link_url=""):
	try:
		if action == "Item":
			action = "PRODUK_DETAIL"
		elif action == "Item Group":
			action = "PRODUK_ITEM_GROUP"
		elif action == "Brand":
			action = "PRODUK_BRAND"
		else:
			action = "GLOBAL"

		# s = get_request_session()
		url = "https://fcm.googleapis.com/fcm/send"
		header = {"Authorization": "key={}".format(FCM),"Content-Type": "application/json"}
		content = {
			"to":"/topics/All_Test",
			"data": {
				"action": action,
				"title": title,
				"body": body,
				"image": image,
				"link_url": link_url
			}
		}
		print(json.dumps(content))
		cmd = '''curl -d '{}' -H "Content-Type: application/json" -H "Authorization: key={}" {}'''.format(json.dumps(content), FCM, url)
		args = shlex.split(cmd)
		process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()
		notification = frappe.get_doc("Notification", name)
		notification.notification_content = json.dumps(content)
		notification.status = "Received"
		notification.save(ignore_permissions=True)
		# frappe.db.commit()
		# res = s.post(url=url,headers=header,data=json.dumps(content),verify=False)
		# return res
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def notification_all_test(name, title, body, image="", action="GLOBAL", link_url=""):
	try:
		if action == "Item":
			action = "PRODUK_DETAIL"
		elif action == "Item Group":
			action = "PRODUK_ITEM_GROUP"
		elif action == "Brand":
			action = "PRODUK_BRAND"
		else:
			action = "GLOBAL"

		# s = get_request_session()
		url = "https://fcm.googleapis.com/fcm/send"
		header = {"Authorization": "key={}".format(FCM),"Content-Type": "application/json"}
		content = {
			"to":"/topics/All_Test",
			"data": {
				"action": action,
				"title": title,
				"body": body,
				"image": image,
				"link_url": link_url
			}
		}
		print(json.dumps(content))
		cmd = '''curl -d '{}' -H "Content-Type: application/json" -H "Authorization: key={}" {}'''.format(json.dumps(content), FCM, url)
		args = shlex.split(cmd)
		process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()
		notification = frappe.get_doc("Notification", name)
		notification.notification_content = json.dumps(content)
		notification.status = "Received"
		notification.save(ignore_permissions=True)
		# frappe.db.commit()
		# res = s.post(url=url,headers=header,data=json.dumps(content),verify=False)
		# return res
	except:
		return error_format(sys.exc_info()[1])

@frappe.whitelist(allow_guest=False)
def notification_test(user):
	try:
		docUser = frappe.get_doc("User", user)
		s = get_request_session()
		url = "https://fcm.googleapis.com/fcm/send"
		header = {"Authorization": "key={}".format(FCM),"Content-Type": "application/json"}
		content = {
				"to":"/topics/All_Test",
				"data": {
						"title": "Testing",
						"body": "halo this is testing",
				}
		}
		print("header " + str(header))
		print("data " + str(content))
		res = s.post(url=url,headers=header,data=json.dumps(content),verify=False)
		return res
	except:
		return error_format(sys.exc_info()[1])

