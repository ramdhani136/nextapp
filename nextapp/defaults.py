import frappe

def get_default_company():
    return frappe.get_value("Global Defaults","Global Defaults","default_company")

def get_default_warehouse():
    return frappe.get_value("Stock Settings","Stock Settings","default_warehouse")

def get_default_cost_center():
    return frappe.get_value("Next Sales Setting","Next Sales Setting","default_cost_center")

def get_default_price_list():
    return frappe.get_value("Selling Settings","Selling Settings","selling_price_list")