#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to conduct audits on users and export the results to csv.
Version:  0.4
Github:   https://github.com/Ripped-Kanga/RingCentral-Scripts
"""
# Import libraries
import os
import sys
import json
import time
import datetime
import csv
from RingCentralMain import connection_test, connectRequest, audit_checker

# Global Variables
start_time = datetime.datetime.now()
user_datalist = []
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

# Receives parsed variable data from audit_checker() and begins audit of users, stores audited data in user_datalist dictionary and parses it to build_user_csv()
def get_ringcentral_users(user_count, built_url):
	resp = connectRequest(built_url)
	
	for record in resp.json().records:
		resp2 = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}')
		data = json.loads(resp2.text())
		ext_name = record.name
		ext_number = record.extensionNumber
		ext_status = record.status
		ext_site = data.get('site', {}).get('name')
		ext_company = data.get('contact', {}).get('company')
		ext_department = data.get('contact', {}).get('department')
		ext_job_title = data.get('contact', {}).get('jobTitle')
		ext_email = data.get('contact', {}).get('email')
		ext_is_admin = data.get('permissions', {}).get('admin', {}).get('enabled')
		ext_setup_wizard = data.get('setupWizardState')
		
		# For Debug
		# print (f'\u2192\u2192Name: {ext_name}\nExt Number: {ext_number} \nExt Status: {ext_status} \nSite: {ext_site}\nCompany: {ext_company}\nDepartment: {ext_department} \nExt Job Title: {ext_job_title} \nExt Email: {ext_email}\nExt has admin?: {ext_is_admin}\nExt Setup?: {ext_setup_wizard}\n')
		
		# Stored audit data.
		user_datalist.append({
			"Extension Name":      	ext_name,
			"Extension Number": 		ext_number,
			"Extension Status":    	ext_status,
			"Site":     						ext_site,
			"Company":							ext_company,
			"Department":						ext_department,
			"Job Title":						ext_job_title,
			"Email":								ext_email,
			"is Administrator?":		ext_is_admin,
			"Setup Wizard State":		ext_setup_wizard
		})

		# Global variable so that user_main() can report the total audited users.
		global user_audit
		user_audit += 1
		print (f'Audited {user_audit} of {user_count} users.')

	#Send the user_datalist dictionary to be written to csv file
	build_user_csv(user_datalist)


#Builds the csv file, sets headers.
def build_user_csv(user_datalist):
	folder_name = 'AuditResults'
	file_name = 'UserAudit.csv'
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)
	file_path = os.path.join(folder_name, file_name)
	datalist_jsondump = json.dumps(user_datalist)
	datalist_user_dict = json.loads(datalist_jsondump)
	with open(file_path, "w", newline='', encoding="utf-8") as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=datalist_user_dict[0].keys())
		writer.writeheader()
		for row in datalist_user_dict:
			writer.writerow(row)
		print (f'Wrote CSV file export to {file_path}')

# Start Execution
if __name__ == "__main__":
	main_user()
