import frappe
import json
from erpnext.stock.get_item_details import get_item_details

def customer_user():
	customer = frappe.get_list("Customer", fields="*", filters={"user": None}, limit=10)
	for row in customer:
		if row["email"] == None:
			username = row["customer_name"].replace(' ','')
			email = username + "@mirage.com"
		else:
			email = row["email"]
		password = email + "mirage123"
		roles_to_apply=[{"role":"Customer"}]
			
		doc = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"full_name": row["customer_name"],
			"first_name": row["customer_name"],
			"send_welcome_email": 0,
			"new_password": password,
			"send_password_update_notification": 0,
			"roles": roles_to_apply
		})
		doc.insert(ignore_permissions=True)

		doc = frappe.get_doc("Customer", row["name"])
		doc.user = email
		doc.email = email
		doc.save(ignore_permissions=True)
	frappe.db.commit()

def total_sales_adjustment():
	items = frappe.get_list("Item", fields="item_code")
	for item in items:
		doc = frappe.get_doc("Item", item["item_code"])
		total_sales = frappe.db.sql("SELECT COUNT(*) AS total_sales FROM `tabSales Invoice Item` sii WHERE sii.item_code = '{}' AND (SELECT status FROM `tabSales Invoice` WHERE name = sii.parent) = 'Paid'".format(item.item_code), as_dict=True)[0]["total_sales"]
		doc.total_sales = total_sales
		doc.save()
		print(item["item_code"] + " - " + str(total_sales))
		frappe.db.commit()

def user_permission():
	customers = frappe.get_list("Customer", fields="*")
	for customer in customers:
		check = frappe.get_all("User Permission",fields="user",filters={"user":("LIKE",customer["user"])})
		if len(check) == 0 and customer["user"] != None:
			doc = frappe.get_doc({
				"doctype":"User Permission",
				"user":customer["user"],
				"allow":"Customer",
				"for_value":customer["name"],
				"apply_to_all_doctypes":1
			})
			doc.insert(ignore_permissions=True)
	frappe.db.commit()

def hide_item():
	items = frappe.get_list("Item", fields="*", filters={"item_name": ("LIKE", "%{}%".format("#"))})
	for item in items:
		args = {
			"item_code": item["item_code"],
			"warehouse": '1.HEAD OFFICE - MI',
			"company": 'CV. Mirage Indonesia',
			"conversion_rate": 1,
			"selling_price_list": "DEALER",
			"price_list_currency": "IDR",
			"plc_conversion_rate": 1,
			"doctype": "Sales Order",
			"transaction_date": frappe.utils.today(),
			"conversion_rate": 1,
			"ignore_pricing_rule": 0
		}
		item_details = get_item_details(args)
		if item_details["projected_qty"] == 0:
			frappe.db.sql("UPDATE `tabItem` SET hide = 1 WHERE name = '{}'".format(item["name"]))
			print(item["item_name"])
	frappe.db.commit()

def projected_qty_item():
	item_list = frappe.get_list("Item", fields="item_code", filters={"item_code": "RPP-37BK"})
	for item in item_list:
		projected_qty = frappe.get_value("Bin", {"item_code": item["item_code"], "warehouse": "1.HEAD OFFICE - MI"}, "projected_qty") or 0
		doc = frappe.get_doc("Item", item["item_code"])
		if doc.projected_quantity != projected_qty:
			doc.projected_quantity = projected_qty
			doc.save(ignore_permissions=True)
			# frappe.db.sql("UPDATE `tabItem` SET projected_quantity = '{}' WHERE item_code = '{}'".format(projected_qty, item["item_code"]))
			print(item["item_code"] + " - " + str(projected_qty))
			frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def raja_ongkir_city():
	if not frappe.get_value("Raja Ongkir", "Indonesia"):
		doc = frappe.get_doc({
			"doctype": "Raja Ongkir",
			"id": 0,
			"territory_name": "Indonesia",
			"type": "Negara",
			"is_group": 1
		})
		doc.insert(ignore_permissions=True)
	from frappe.utils import get_request_session
	request = get_request_session()
	url = "https://pro.rajaongkir.com/api/province"
	header = {
		"key": "ccd4a7840666a7b9853c6aef499747a5"
	}
	response = request.get(url=url,headers=header,verify=False)
	response = json.loads(response.content.decode('utf-8'))
	for province in response["rajaongkir"]["results"]:
		if not frappe.get_value("Raja Ongkir", province["province"]):
			doc = frappe.get_doc({
				"doctype": "Raja Ongkir",
				"id": province["province_id"],
				"territory_name": province["province"],
				"type": "Provinsi",
				"is_group": 1,
				"parent_raja_ongkir": "Indonesia",
				"parent_tree": "Indonesia",
				"old_parent": "Indonesia"
			})
			doc.insert(ignore_permissions=True)
		else:
			doc = frappe.get_doc("Raja Ongkir", province["province"])
			doc.territory_name = province["province"]
			doc.type = "Provinsi"
			doc.is_group = 1
			doc.parent_raja_ongkir = "Indonesia"
			doc.parent_tree = "Indonesia"
			doc.old_parent = "Indonesia"
			doc.save(ignore_permissions=True)
	frappe.db.commit()

	request = get_request_session()
	url = "https://pro.rajaongkir.com/api/city"
	header = {
		"key": "ccd4a7840666a7b9853c6aef499747a5"
	}
	response = request.get(url=url,headers=header,verify=False)
	response = json.loads(response.content.decode('utf-8'))
	city_list = []
	for city in response["rajaongkir"]["results"]:
		if city["city_name"] in city_list:
			print(city["city_name"] + " " + city["type"])
			if not frappe.get_value("Raja Ongkir", city["city_name"] + " " + city["type"]):
				doc = frappe.get_doc({
					"doctype": "Raja Ongkir",
					"id": city["city_id"],
					"territory_name": city["city_name"] + " " + city["type"],
					"type": city["type"],
					"is_group": 1,
					"parent_raja_ongkir": city["province"],
					"parent_tree": city["province"],
					"old_parent": city["province"]
				})
				doc.insert(ignore_permissions=True)
			else:
				doc = frappe.get_doc("Raja Ongkir", city["city_name"] + " " + city["type"])
				doc.territory_name = city["city_name"] + " " + city["type"]
				doc.type = city["type"]
				doc.is_group = 1
				doc.parent_raja_ongkir = city["province"]
				doc.parent_tree = city["province"]
				doc.old_parent = city["province"]
				doc.save(ignore_permissions=True)
		else:
			if not frappe.get_value("Raja Ongkir", city["city_name"]):
				doc = frappe.get_doc({
					"doctype": "Raja Ongkir",
					"id": city["city_id"],
					"territory_name": city["city_name"],
					"type": city["type"],
					"is_group": 1,
					"parent_raja_ongkir": city["province"],
					"parent_tree": city["province"],
					"old_parent": city["province"]
				})
				doc.insert(ignore_permissions=True)
			else:
				doc = frappe.get_doc("Raja Ongkir", city["city_name"])
				doc.territory_name = city["city_name"]
				doc.type = city["type"]
				doc.is_group = 1
				doc.parent_raja_ongkir = city["province"]
				doc.parent_tree = city["province"]
				doc.old_parent = city["province"]
				doc.save(ignore_permissions=True)

		city_list.append(city["city_name"])

	frappe.db.commit()
	return True

@frappe.whitelist(allow_guest=True)
def raja_ongkir_subdistrict():
	from frappe.utils import get_request_session
	city_list = frappe.db.sql("SELECT * FROM `tabRaja Ongkir` WHERE type = 'Kabupaten' OR type = 'Kota'", as_dict=True)
	for city in city_list:
		request = get_request_session()
		url = "https://pro.rajaongkir.com/api/subdistrict?city=" + city["id"]
		header = {
			"key": "ccd4a7840666a7b9853c6aef499747a5"
		}
		response = request.get(url=url,headers=header,verify=False)
		response = json.loads(response.content.decode('utf-8'))
		for subdistrict in response["rajaongkir"]["results"]:
			if not frappe.get_value("Raja Ongkir", subdistrict["subdistrict_name"]):
				doc = frappe.get_doc({
					"doctype": "Raja Ongkir",
					"id": subdistrict["subdistrict_id"],
					"territory_name": subdistrict["subdistrict_name"],
					"type": "Kecamatan",
					"is_group": 0,
					"parent_raja_ongkir": subdistrict["city"],
					"parent_tree": subdistrict["city"],
					"old_parent": subdistrict["city"]
				})
				doc.insert(ignore_permissions=True)
			else:
				doc = frappe.get_doc("Raja Ongkir", subdistrict["subdistrict_name"])
				doc.territory_name = subdistrict["subdistrict_name"]
				doc.type = "Kecamatan"
				doc.is_group = 0
				doc.parent_raja_ongkir = subdistrict["city"]
				doc.parent_tree = subdistrict["city"]
				doc.old_parent = subdistrict["city"]
				doc.save(ignore_permissions=True)
		frappe.db.commit()

	return True

@frappe.whitelist(allow_guest=True)
def territory_subdistrict():
	from frappe.utils import get_request_session
	city_list = frappe.db.sql("SELECT * FROM `tabTerritory` WHERE raja_ongkir_id IS NOT NULL AND is_group = 0 AND territory_name NOT LIKE '%,%'", as_dict=True)
	for city in city_list:
		print(city["name"])
		request = get_request_session()
		url = "https://pro.rajaongkir.com/api/subdistrict?city=" + city["raja_ongkir_id"]
		header = {
			"key": "ccd4a7840666a7b9853c6aef499747a5"
		}
		response = request.get(url=url,headers=header,verify=False)
		response = json.loads(response.content.decode('utf-8'))
		for subdistrict in response["rajaongkir"]["results"]:
			print(" - " + subdistrict["subdistrict_name"].upper() + " / " + subdistrict["subdistrict_id"])
			if not frappe.get_value("Territory", city["name"] + ", " + subdistrict["subdistrict_name"].upper()):
				doc = frappe.get_doc({
					"doctype": "Territory",
					"raja_ongkir_id": subdistrict["subdistrict_id"],
					"territory_name": city["name"] + ", " + subdistrict["subdistrict_name"].upper(),
					"hide": 0,
					"is_group": 0,
					"parent_territory": city["name"],
					"old_parent": city["name"]
				})
				doc.insert(ignore_permissions=True)
			else:
				doc = frappe.get_doc("Territory", city["name"] + ", " + subdistrict["subdistrict_name"].upper())
				doc.territory_name = city["name"] + ", " + subdistrict["subdistrict_name"].upper()
				doc.parent_territory = city["name"]
				doc.old_parent = city["name"]
				doc.save(ignore_permissions=True)

			territory = frappe.get_doc("Territory", city["name"])
			territory.is_group = 1
			territory.save(ignore_permissions=True)

		frappe.db.commit()

	return True

@frappe.whitelist(allow_guest=True)
def random_item_price():
	# item_price_list = frappe.db.sql("SELECT name, item_code, COUNT(*) as counter FROM `tabItem Price` GROUP BY item_code HAVING counter > 1", as_dict=True)
	# for ip in item_price_list:
	# 	frappe.delete_doc("Item Price", ip["name"])
	# 	print(ip["name"])
	# frappe.db.commit()
	import random
	item_price_list = frappe.get_list("Item Price", fields="name", filters={"name": "ITEM-PRICE-11332"})
	for ip in item_price_list:
		item_price = frappe.get_doc("Item Price", ip["name"])
		item_price.price_list_rate = 1#random.randint(10000,100000)
		item_price.save()
		print(ip["name"])
	frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def cart_item_weight():
	shopping_cart_item_list = frappe.get_list("Shopping Cart Item", fields="*")
	for sci in shopping_cart_item_list:
		print(str(sci["weight_per_unit"]))
		weight_per_unit = frappe.get_value("Item", sci["item"], "weight_per_unit")
		print(str(weight_per_unit))
		frappe.db.sql("UPDATE `tabShopping Cart Item` SET weight_per_unit = {} WHERE name = '{}'".format(weight_per_unit, sci["name"]))
	frappe.db.commit()

def delete_territory():
	territory_list = frappe.get_list("Territory", fields="*")
	for t in territory_list:
		print(t["name"])
		frappe.delete_doc("Territory", t["name"])
	frappe.db.commit()

def territory_city():
	from frappe.utils import get_request_session
	request = get_request_session()
	url = "https://pro.rajaongkir.com/api/city"
	header = {
		"key": "ccd4a7840666a7b9853c6aef499747a5"
	}
	response = request.get(url=url,headers=header,verify=False)
	response = json.loads(response.content.decode('utf-8'))
	for city in response["rajaongkir"]["results"]:
		city_id = frappe.get_value("Territory", {"raja_ongkir_id": city["city_id"], "is_group": 1}, "raja_ongkir_id")
		if not city_id:
			city_name = city["city_name"].upper() + " " + city["type"].upper()
			if city["province"].upper() == "NANGGROE ACEH DARUSSALAM (NAD)":
				city["province"] = "ACEH"
			elif city["province"].upper() == "NUSA TENGGARA BARAT (NTB)":
				city["province"] = "NTB"
			elif city["province"].upper() == "NUSA TENGGARA TIMUR (NTT)":
				city["province"] = "NTT"
			if not frappe.get_value("Territory", city_name):
				doc = frappe.get_doc({
					"doctype": "Territory",
					"raja_ongkir_id": city["city_id"],
					"territory_name": city_name,
					"hide": 0,
					"is_group": 1,
					"parent_territory": city["province"].upper(),
					"old_parent": city["province"].upper()
				})
				doc.insert(ignore_permissions=True)
			else:
				doc = frappe.get_doc("Territory", city_name)
				doc.territory_name = city_name
				doc.parent_territory = city["province"].upper()
				doc.old_parent = city["province"].upper()
				doc.save(ignore_permissions=True)
			print(city_name)

			request = get_request_session()
			url = "https://pro.rajaongkir.com/api/subdistrict?city=" + city["city_id"]
			header = {
				"key": "ccd4a7840666a7b9853c6aef499747a5"
			}
			responseSubdistrict = request.get(url=url,headers=header,verify=False)
			responseSubdistrict = json.loads(responseSubdistrict.content.decode('utf-8'))
			for subdistrict in responseSubdistrict["rajaongkir"]["results"]:
				print(city_name + " - " + subdistrict["subdistrict_name"].upper() + " / " + subdistrict["subdistrict_id"])
				if not frappe.get_value("Territory", city_name + ", " + subdistrict["subdistrict_name"].upper()):
					doc = frappe.get_doc({
						"doctype": "Territory",
						"raja_ongkir_id": subdistrict["subdistrict_id"],
						"territory_name": city_name + ", " + subdistrict["subdistrict_name"].upper(),
						"hide": 0,
						"is_group": 0,
						"parent_territory": city_name,
						"old_parent": city_name
					})
					doc.insert(ignore_permissions=True)
				else:
					doc = frappe.get_doc("Territory", city_name + ", " + subdistrict["subdistrict_name"].upper())
					doc.territory_name = city_name + ", " + subdistrict["subdistrict_name"].upper()
					doc.parent_territory = city_name
					doc.old_parent = city_name
					doc.save(ignore_permissions=True)

			frappe.db.commit()
	return True

@frappe.whitelist(allow_guest=True)
def territory_subdistrict():
	from frappe.utils import get_request_session
	city_list = frappe.db.sql("SELECT * FROM `tabTerritory` WHERE raja_ongkir_id IS NOT NULL AND is_group = 0 AND territory_name NOT LIKE '%,%'", as_dict=True)
	for city in city_list:
		print(city["name"])
		request = get_request_session()
		url = "https://pro.rajaongkir.com/api/subdistrict?city=" + city["raja_ongkir_id"]
		header = {
			"key": "ccd4a7840666a7b9853c6aef499747a5"
		}
		response = request.get(url=url,headers=header,verify=False)
		response = json.loads(response.content.decode('utf-8'))
		for subdistrict in response["rajaongkir"]["results"]:
			print(" - " + subdistrict["subdistrict_name"].upper() + " / " + subdistrict["subdistrict_id"])
			if not frappe.get_value("Territory", city["name"] + ", " + subdistrict["subdistrict_name"].upper()):
				doc = frappe.get_doc({
					"doctype": "Territory",
					"raja_ongkir_id": subdistrict["subdistrict_id"],
					"territory_name": city["name"] + ", " + subdistrict["subdistrict_name"].upper(),
					"hide": 0,
					"is_group": 0,
					"parent_territory": city["name"],
					"old_parent": city["name"]
				})
				doc.insert(ignore_permissions=True)
			else:
				doc = frappe.get_doc("Territory", city["name"] + ", " + subdistrict["subdistrict_name"].upper())
				doc.territory_name = city["name"] + ", " + subdistrict["subdistrict_name"].upper()
				doc.parent_territory = city["name"]
				doc.old_parent = city["name"]
				doc.save(ignore_permissions=True)

			territory = frappe.get_doc("Territory", city["name"])
			territory.is_group = 1
			territory.save(ignore_permissions=True)

		frappe.db.commit()

	return True