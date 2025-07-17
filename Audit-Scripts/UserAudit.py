#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to conduct audits on users. 
Version:  0.3
Github:   https://github.com/Ripped-Kanga/RingCentral-Scripts
"""
# Import libraries
import os
import sys
import json
import time
import datetime
from RingCentralMain import connection_test, connectRequest, audit_checker

# Global Variables
start_time = datetime.datetime.now()

# Start main thread
def main_user():
	print (f'Script Start Time: {start_time}')
	connection_attempt = connection_test()
	if connection_attempt:
		print ("Proceeding with User Audit, note that as a minimum, the 'User' type is already filtered for.")
		user_count, built_url = audit_checker('/restapi/v1.0/account/~/extension?type=User')
		get_ringcentral_users(built_url)
	else:
		sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")


def get_ringcentral_users(built_url):
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
		print (f'\u2192\u2192Name: {ext_name}\nExt Number: {ext_number} \nExt Status: {ext_status} \nSite: {ext_site}\nCompany: {ext_company}\nDepartment: {ext_department} \nExt Job Title: {ext_job_title} \nExt Email: {ext_email}\nExt has admin?: {ext_is_admin}\nExt Setup?: {ext_setup_wizard}\n')



'''
def build_datalist():

  user_datalist.append({
    "ID":      				<placeholder>,
    "User Name": 			<placeholder>,
    "User Extension": <placeholder>,
    "User DID":     	<placeholder>,
    "Status":					<placeholder>
  })
  build_csv(datalist)

# Builds the csv file, sets headers. 
def build_csv(datalist):
    datalist_jsondump = json.dumps(datalist)
    datalist_json = json.loads(datalist_jsondump)
    with open("callQueues.csv", "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=datalist_json[0].keys())
        writer.writeheader()
        for row in datalist_json:
          #enable below print for debugging
          #print (row['Call Queue Name'], row['Call Queue Extension'], row['Call Queue Member'], row['Member Extension'])
          writer.writerow(row)
'''


# Start Execution
if __name__ == "__main__":
	main_user()
