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
from RingCentralMain import *

# Global Variables
start_time = datetime.datetime.now()
datalist = []
cq_datalist = []
user_audit = 0

# Start main thread, this handles connection test, as well as parsing returned variable data from audit_checker().
def audit_start():
	housekeeping()
	print (f'Script Start Time: {start_time}')
	connection_attempt = connection_test()
	if connection_attempt:
		print ("\nProceeding with User Audit\n")
		filter_user_count, user_count, built_url = audit_checker('/restapi/v1.0/account/~/extension')
		get_ringcentral_extensions(filter_user_count, user_count, built_url)
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
def get_ringcentral_extensions(filter_user_count, user_count, built_url):
	(
		csv_field_id,
		csv_field_name,
		csv_field_number,
		csv_field_did,
		csv_field_status,
		csv_field_type,
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

	# Initialise variables with default values.
	(
		ext_id,
		ext_name,
		ext_number,
		ext_did,
		ext_status,
		ext_type,
		ext_site,
		ext_company,
		ext_department,
		ext_job_title,
		ext_email,
		ext_dnd_status,
		ext_bhr_fw_dest,
		ext_ahr_fw_dest,
		ext_assigned_role,
		ext_is_admin,
		ext_setup_wizard,
		ext_device_name,
		ext_device_model,
		ext_device_serial,
		ext_device_status,
		cq_bhr_fw_dest,
		cq_bhr_fw_type
		) = [None] * 23

	resp = connectRequest(built_url)
	# Loop through returned records and extract User IDs to build GET Extension URI.
	for record in resp.json().records:
		user_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}')
		user_data = json.loads(user_resp.text())

		# Check if user selected direct number field for csv export, retrieve info from API and set variables.
		if csv_field_did:
			user_did_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/phone-number?usageType=DirectNumber')
			if user_did_resp:
				user_did_data = json.loads(user_did_resp.text())
				for phone_record in user_did_data['records']:
					if phone_record.get('primary'):
						ext_did = phone_record.get('phoneNumber')
						break
					else:
						ext_did = None
			else:
				ext_did = None

		# Check if user has selected user assigned role
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
		# Call Queues return additional JSON that must be filtered for. 
		if csv_field_bhr_fw:
			bh_forwarding_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/answering-rule/business-hours-rule')
			if bh_forwarding_resp != None:
				bh_forwarding_data = json.loads(bh_forwarding_resp.text())
				bhr_missed_call_forward = bh_forwarding_data.get('missedCall')
				bhr_voicemail = bh_forwarding_data.get('voicemail', {}).get('enabled')

				# Check if the extension type is a call queue and process differently. 
				if user_data.get('type') == "Department":
					bh_fwd_cq_data = bh_forwarding_data.get('queue', {})
					bh_fwd_cq_holdTimerAction = bh_forwarding_data.get('queue', {}).get('holdTimeExpirationAction')

					# Checks if transfer type is "To Extension"
					if bh_fwd_cq_holdTimerAction == "TransferToExtension":
						cq_fwd_ext_data = bh_forwarding_data.get('queue', {}).get('transfer')
						for call_queue_transfer_exts in cq_fwd_ext_data:
							if call_queue_transfer_exts.get('action') == "HoldTimeExpiration":
								cq_fwd_ext = call_queue_transfer_exts.get('extension', {}).get('name')
								ext_bhr_fw_dest = cq_fwd_ext
								cq_bhr_fw_dest = cq_fwd_ext
								cq_bhr_fw_type = 'Transfer to Extension'

					# Check if transfer type is "To Voicemail"
					elif bh_fwd_cq_holdTimerAction == "Voicemail":
						ext_bhr_fw_dest = 'Call Queue Voicemail'
						cq_bhr_fw_dest = 'Call Queue Voicemail'
						cq_bhr_fw_type = 'Call Queue Voicemail'

					# Check if transfer type is "To External Number"
					elif bh_fwd_cq_holdTimerAction == "UnconditionalForwarding":
						bh_fwd_cq_external = bh_fwd_cq_data.get('unconditionalForwarding')
						for ext_number in bh_fwd_cq_external:
							cq_fwd_external_dest = ext_number.get('phoneNumber')
							ext_bhr_fw_dest = cq_fwd_external_dest
							cq_bhr_fw_dest = cq_fwd_external_dest
							cq_bhr_fw_type = "External Number"

					# Catch unknown values
					else:
						ext_bhr_fw_dest == "Unknown"

				# Check if extension has business hours rule call forward or voicemail, set variables.
				elif user_data.get('type') == "User" and bhr_voicemail:
					ext_bhr_fw_dest = 'User Voicemail'
				elif user_data.get('type') == "User" and bhr_missed_call_forward:
					# check if it is an internal or external forward
					dest_type = bh_forwarding_data.get('missedCall', {}).get('actionType')
					if dest_type == 'ConnectToExtension':
						ext_bhr_internal_fw_id = bh_forwarding_data.get('missedCall', {}).get('extension', {}).get('id')
						check_fw_destination_int_name = connectRequest(f'/restapi/v1.0/account/~/extension/{ext_bhr_internal_fw_id}')
						fw_destination_internal_name_data = json.loads(check_fw_destination_int_name.text())
						ext_bhr_fw_dest = fw_destination_internal_name_data.get('name')
					elif dest_type == 'ConnectToExternalNumber':
						ext_bhr_fw_dest = bh_forwarding_data.get('missedCall', {}).get('externalNumber', {}).get('phoneNumber')
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
				ext_ahr_fw_dest = "No After Hours Rule Exists"


		# If user selected device field for csv export, retrieve info from API and set variables.
		if csv_field_device_info:
			device_resp = connectRequest(f'/restapi/v1.0/account/~/extension/{record.id}/device?type=HardPhone')
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

		# If the user included call queues as a specific API filter, build another dict and export to seperate AuditCallQueue.csv file which includes call queue members.
		if user_data.get('type') == "Department":
			resp = connectRequest('/restapi/v1.0/account/~/call-queues/'+str(record.id)+'/presence')
			call_queue_members = json.loads(resp.text())

			# Initialise default variable values to protect against loop crash if a call queue has no members.
			cq_member = str('No member')
			cq_member_ext = ''
			cq_member_accept_current_queue_calls = ''
			cq_member_accept_calls = ''

			for member in call_queue_members['records']:
				
				cq_member = member.get('member', {}).get('name')
				if cq_member:
					cq_member_ext = member.get('member', {}).get('extensionNumber')					
					cq_member_accept_calls = member.get('acceptQueueCalls')
					cq_member_accept_current_queue_calls = member.get('acceptCurrentQueueCalls')
				else:
					cq_member = str('No member')
					cq_member_ext = ''
					cq_member_accept_current_queue_calls = ''
					cq_member_accept_calls = ''
				cq_row = {
					"Call Queue Name":      				user_data.get('name'),
					"Call Queue Extension": 				user_data.get('extensionNumber'),
					"Call Queue Member":    				cq_member,
					"Member Extension":     				cq_member_ext,
					"Accept Queue Calls?":					cq_member_accept_calls,
					"Accept Current Queue Calls?":			cq_member_accept_current_queue_calls,
					"Forward Destination Type":				cq_bhr_fw_type,
					"Forward Destination":					cq_bhr_fw_dest
				}
				
				cq_datalist.append(cq_row)
				

		# Set User API variables.
		ext_id = record.id
		ext_name = user_data.get('name')
		ext_number = user_data.get('extensionNumber')
		ext_status = user_data.get('status')
		ext_type = user_data.get('type')
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
			**({"Extension Direct Number": ext_did} if csv_field_did else {}),
			**({"Extension Status":	ext_status} if csv_field_status else {}),
			**({"Extension Type":	ext_type} if csv_field_type else {}),
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
			pprint.pprint(row, indent=2, sort_dicts=False)
		else:
			print (f'\nAudited {user_audit} of {user_count} users.\n')
			print (f'### {ext_name} ###')
			pprint.pprint(row, indent=2, sort_dicts=False)

		#Parse the datalist dictionary to be written to csv file
		build_csv(datalist)
		if user_data.get('type') == "Department":
			cq_build_csv(cq_datalist)

# Start Execution
if __name__ == "__main__":
	# Start audit_start() and listen for keyboard interrupts
	try:
		audit_start()
	except KeyboardInterrupt:
		print('\nInterrupted by keyboard CTRL + C, exiting...\n')
		try:
			sys.exit(130)
		except SystemExit:
			os._exit(130)
