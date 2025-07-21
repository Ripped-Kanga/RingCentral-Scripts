#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to conduct audits on users and export the results to csv.
Version:  0.6
Github:   https://github.com/Ripped-Kanga/RingCentral-Scripts
"""
# Import libraries
import os
import sys
import json
import time
import datetime
import csv
import pprint
from RingCentralMain import connection_test, connectRequest, audit_checker

# Global Variables
start_time = datetime.datetime.now()
datalist = []
user_audit = 0

# Start main thread, this handles connection test, as well as parsing returned variable data from audit_checker().
def main_user():
	print (f'Script Start Time: {start_time}')
	connection_attempt = connection_test()
	if connection_attempt:
		print ("Proceeding with User Audit, note that as a minimum, the 'User' type is already filtered for.")
		user_count, built_url = audit_checker('/restapi/v1.0/account/~/extension?type=User')
		get_ringcentral_users(user_count, built_url)
	else:
		sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")

	end_time = datetime.datetime.now()
	runtime = (end_time - start_time).total_seconds()
	m, s  = divmod(runtime, 60)

	print ("Script has completed, audit results:")
	print (f'Audited {user_audit} users of {user_count} found users.')
	print (f'\nScript End Time:    {end_time}')
	print ("Script runtime was: {} minutes and {} seconds".format(int(m), int(s)))
	exit (0)

# Receives parsed variable data from audit_checker() and begins audit of users, stores audited data in datalist dictionary and parses it to build_user_csv()
def get_ringcentral_users(user_count, built_url):
	resp = connectRequest(built_url)
	for record in resp.json().records:
		resp2 = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}')
		resp3 = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/device')
		user_data = json.loads(resp2.text())
		device_data = json.loads(resp3.text())
		device_records = device_data['records']

		ext_id = record.id
		ext_name = record.name
		ext_number = record.extensionNumber
		ext_status = record.status
		ext_site = user_data.get('site', {}).get('name')
		ext_company = user_data.get('contact', {}).get('company')
		ext_department = user_data.get('contact', {}).get('department')
		ext_job_title = user_data.get('contact', {}).get('jobTitle')
		ext_email = user_data.get('contact', {}).get('email')
		ext_is_admin = user_data.get('permissions', {}).get('admin', {}).get('enabled')
		ext_setup_wizard = user_data.get('setupWizardState')
		
		# Store user and device audit data, if the user has a device, store the device values, otherwise store blank device values.
		if device_records:
			for device in device_records:
				row = {
					"Extension Name":				ext_name,
					"Extension Number":			ext_number,
					"Extension Status":			ext_status,
					"Site":									ext_site,
					"Company":							ext_company,
					"Department":						ext_department,
					"Job Title":						ext_job_title,
					"Email":								ext_email,
					"is Administrator?":		ext_is_admin,
					"Setup Wizard State":		ext_setup_wizard,
					"Device Name":					device.get('name'),
					"Device Model":					device.get('model', {}).get('name'),
					"Device Serial":				device.get('serial'),
					"Device Status":				device.get('status')
				}
				datalist.append(row)
		else:
			row = {
			"Extension Name":				ext_name,
			"Extension Number":			ext_number,
			"Extension Status":			ext_status,
			"Site":									ext_site,
			"Company":							ext_company,
			"Department":						ext_department,
			"Job Title":						ext_job_title,
			"Email":								ext_email,
			"is Administrator?":		ext_is_admin,
			"Setup Wizard State":		ext_setup_wizard,
			"Device Name":					"",
			"Device Model":					"",
			"Device Serial":				"",
			"Device Status":				""
		}
			datalist.append(row)

		# Global variable so that user_main() can report the total audited users.
		global user_audit
		user_audit += 1

		print (f'Audited {user_audit} of {user_count} users.')

	#Send the datalist dictionary to be written to csv file
	build_user_csv(datalist)

#Builds the csv file, sets headers.
def build_user_csv(datalist):
	folder_name = 'AuditResults'
	file_name = 'UserAudit.csv'
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)
	file_path = os.path.join(folder_name, file_name)

	if not datalist:
		print ("No data in dictionary to write")
		return

	fieldnames = list(datalist[0].keys())
	with open(file_path, "w", newline='', encoding="utf-8") as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
		writer.writeheader()
		for row in datalist:
			writer.writerow(row)

			#print (f'Wrote CSV row export to {file_path}')

# Start Execution
if __name__ == "__main__":
	main_user()
