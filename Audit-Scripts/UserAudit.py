#!/usr/bin/python
__version__ = "0.91"

# Import libraries
import os
import sys
import json
import time
import datetime
import csv
import pprint
from RingCentralMain import housekeeping, connection_test, connectRequest, audit_checker, prep_user_csv

# Global Variables
start_time = datetime.datetime.now()
datalist = []
user_audit = 0

# Start main thread, this handles connection test, as well as parsing returned variable data from audit_checker().
def main_user():
	housekeeping()
	print (f'Script Start Time: {start_time}')
	connection_attempt = connection_test()
	if connection_attempt:
		print ("\nProceeding with User Audit\n")
		filter_user_count, user_count, built_url = audit_checker('/restapi/v1.0/account/~/extension')
		get_ringcentral_users(filter_user_count, user_count, built_url)
	else:
		sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")

	end_time = datetime.datetime.now()
	runtime = (end_time - start_time).total_seconds()
	m, s  = divmod(runtime, 60)

	print ("Script has completed, audit results:")
	if filter_user_count:
		print(f'Audited {user_audit} users of {filter_user_count} found filtered users.')
	else:
		print (f'Audited {user_audit} users of {user_count} found users.')
	print (f'\nScript End Time:    {end_time}')
	print ("Script runtime was: {} minutes and {} seconds".format(int(m), int(s)))
	exit (0)

# Receives parsed variable data from audit_checker() and begins audit of users, stores audited data in datalist dictionary and parses it to build_user_csv()
def get_ringcentral_users(filter_user_count, user_count, built_url):
	(
		csv_field_id,
		csv_field_name,
		csv_field_number,
		csv_field_status,
		csv_field_type,
		csv_field_subType,
		csv_field_site,
		csv_field_company,
		csv_field_department,
		csv_field_job_title,
		csv_field_email,
		csv_field_admin_check,
		csv_field_user_assigned_role,
		csv_field_setup_wizard_status,
		csv_field_dnd_state,
		csv_field_bhr_fw,
		csv_field_ahr_fw,
		csv_field_device_info
	) = prep_user_csv()

	resp = connectRequest(built_url)
	# Loop through returned records and extract User IDs to build GET Extension URI.
	for record in resp.json().records:
		user_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}')
		user_data = json.loads(user_resp.text())

		# Check if user has role assigned, set variable.
		if csv_field_user_assigned_role:
			user_role_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/assigned-role')
			user_roles_list = user_role_resp.json().records
			if user_roles_list:
				for roles in user_roles_list:
					ext_assigned_role = roles.displayName
			else:
				ext_assigned_role = None

		# If user selected dnd_state field for csv export, retrieve info from API and set variables.
		if csv_field_dnd_state:
			user_presence_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/presence')
			user_presence_data = json.loads(user_presence_resp.text())
			ext_dnd_status = user_presence_data.get('dndStatus')

		# If user selected Business Hours Forward Destination field for csv export, retireve info from API and set variables.
		if csv_field_bhr_fw:
			user_bh_forwarding_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/answering-rule/business-hours-rule')
			if user_bh_forwarding_resp != None:
				user_bh_forwarding_data = json.loads(user_bh_forwarding_resp.text())
				bhr_missed_call_forward = user_bh_forwarding_data.get('missedCall')
				bhr_voicemail = user_bh_forwarding_data.get('voicemail', {}).get('enabled')

				# Check if extension has business hours rule call forward or voicemail, set variables.
				if bhr_voicemail == True:
					ext_bhr_fw_dest = 'User Voicemail'
				elif bhr_missed_call_forward:
					# check if it is an internal or external forward
					dest_type = user_bh_forwarding_data.get('missedCall', {}).get('actionType')
					if dest_type == 'ConnectToExtension':
						ext_bhr_int_fw_id = user_bh_forwarding_data.get('missedCall', {}).get('extension', {}).get('id')
						check_fw_destination_int_name = connectRequest(f'/restapi/v1.0/account/~/extension/{ext_bhr_int_fw_id}')
						fw_destination_int_name_data = json.loads(check_fw_destination_int_name.text())
						ext_bhr_fw_dest = fw_destination_int_name_data.get('name')
					elif dest_type == 'ConnectToExternalNumber':
						ext_bhr_fw_dest = user_bh_forwarding_data.get('missedCall', {}).get('externalNumber', {}).get('phoneNumber')
				else:
					ext_bhr_fw_dest = "No Business Hours Rule Exists"
			else:
				ext_bhr_fw_dest = "No Business Hours Rule"

		# If user selected After Hours Forward Destination field for csv export, retrieve info from API and set variables.
		if csv_field_ahr_fw:
			user_ah_forwarding_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/answering-rule/after-hours-rule')

			if user_ah_forwarding_resp != None:
				user_ah_forwarding_data = json.loads(user_ah_forwarding_resp.text())
				ahr_mode = user_ah_forwarding_data.get('callHandlingAction')
				ahr_transfer_ext_id = user_ah_forwarding_data.get('transfer', {}).get('extension', {}).get('id')
				ahr_voicemail = user_ah_forwarding_data.get('voicemail', {}).get('enabled')

				# Check the forwarding mode switch.
				if ahr_mode == "TakeMessagesOnly":
					ext_ahr_fw_dest = "User Voicemail"
				elif ahr_mode == "TransferToExtension":
					ahr_transfer_ext_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{ahr_transfer_ext_id}')
					ahr_transfer_ext_data = json.loads(ahr_transfer_ext_resp.text())
					ext_ahr_fw_dest = ahr_transfer_ext_data.get('name')
				elif ahr_mode == "UnconditionalForwarding":
					ext_ahr_fw_dest = user_ah_forwarding_data.get('unconditionalForwarding', {}).get('phoneNumber')
				elif ahr_mode == "PlayAnnouncementOnly":
					ext_ahr_fw_dest = "Play Announcement Message"
				elif ahr_mode == "ForwardCalls":
					ext_ahr_fw_dest = "Ring Devices"
				else:
					ext_ahr_fw_dest = "DEBUG"
			else:
				ext_ahr_fw_dest = "No After Hours Rule"


		# If user selected device field for csv export, retrieve info from API and set variables.
		if csv_field_device_info:
			device_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/device')
			device_data = json.loads(device_resp.text())
			device_records = device_data['records']
			if device_records:
				for device in device_records:
					ext_device_name = device.get('name')
					ext_device_model = device.get('model', {}).get('name')
					ext_device_serial = device.get('serial')
					ext_device_status = device.get('status')
			else:
				ext_device_name = "No Device"
				ext_device_model = "No Device"
				ext_device_serial = "No Device"
				ext_device_status = "No Device"

		# Set User API variables.
		ext_id = record.id
		ext_name = user_data.get('name')
		ext_number = user_data.get('extensionNumber')
		ext_status = user_data.get('status')
		ext_type = user_data.get('type')
		ext_subType = user_data.get('subType')
		ext_site = user_data.get('site', {}).get('name')
		ext_company = user_data.get('contact', {}).get('company')
		ext_department = user_data.get('contact', {}).get('department')
		ext_job_title = user_data.get('contact', {}).get('jobTitle')
		ext_email = user_data.get('contact', {}).get('email')
		ext_is_admin = user_data.get('permissions', {}).get('admin', {}).get('enabled')
		ext_setup_wizard = user_data.get('setupWizardState')
		
		
		# Store user and device audit data
		row = {
			**({"User ID": ext_id} if csv_field_id else {}),
			**({"Extension Name": ext_name} if csv_field_name else {}),
			**({"Extension Number": ext_number} if csv_field_number else {}),
			**({"Extension Status":	ext_status} if csv_field_status else {}),
			**({"Extension Type":	ext_type} if csv_field_type else {}),
			**({"Extension Sub Type":	ext_subType} if csv_field_subType else {}),
			**({"Site": ext_site} if csv_field_site else {}),
			**({"Company": ext_company} if csv_field_company else {}),
			**({"Department": ext_department} if csv_field_department else {}),
			**({"Job Title": ext_job_title} if csv_field_job_title else {}),
			**({"Email": ext_email} if csv_field_email else {}),
			**({"DND Status": ext_dnd_status} if csv_field_dnd_state else {}),
			**({"Business Hours Forward Destination": ext_bhr_fw_dest} if csv_field_bhr_fw else {}),
			**({"After Hours Forward Destination": ext_ahr_fw_dest} if csv_field_ahr_fw else {}),
			**({"User Assigned Role": ext_assigned_role} if csv_field_user_assigned_role else {}),
			**({"Is administrator?": ext_is_admin} if csv_field_admin_check else {}),
			**({"Setup Wizard State": ext_setup_wizard} if csv_field_setup_wizard_status else {}),
			**({"Device Name": ext_device_name} if csv_field_device_info else {}),
			**({"Device Model":	ext_device_model} if csv_field_device_info else {}),
			**({"Device Serial": ext_device_serial} if csv_field_device_info else {}),
			**({"Device Status": ext_device_status} if csv_field_device_info else {})
		}
		datalist.append(row)
		
		# Global variable user_audit so that user_main() can report the total audited users.
		global user_audit
		user_audit += 1
		if filter_user_count:
			print (f'\nAudited {user_audit} of {filter_user_count} filtered users.\n')
			print (f'### {ext_name} ###')
			pprint.pprint(row, indent=4, sort_dicts=False)
		else:
			print (f'\nAudited {user_audit} of {user_count} users.\n')
			print (f'### {ext_name} ###')
			pprint.pprint(row, indent=4, sort_dicts=False)

		#Parse the datalist dictionary to be written to csv file
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

# Start Execution
if __name__ == "__main__":
	#start main_user() and listen for keyboard interrupts
	try:
		main_user()
	except KeyboardInterrupt:
		print('\nInterrupted by keyboard CTRL + C, exiting...\n')
		try:
			sys.exit(130)
		except SystemExit:
			os._exit(130)
