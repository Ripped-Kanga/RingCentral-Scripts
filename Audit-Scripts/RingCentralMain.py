#!/usr/bin/python

__author__ = "Alan Saunders"
__purpose__ = "Uses the RingCentral API to collect information on the instance, useful for conducting audits and health checks on RingCentral instances."
__core_version__ = "0.97 - alpha"
__version__ = "0.75"
__github__ = "https://github.com/Ripped-Kanga/RingCentral-Scripts\n"
__disclaimer__ = "The purpose of this project is to provide easy auditability to the RingCentral platform. All the API calls made in this project are GET requests and represent no danger to the RingCentral data. To exit the script at any time, use CTRL + C. All data collected by this tool is writen to CSV file, the file is stored in the /AuditResults folder."

# Import libraries
import os
import sys
import json
import time
import datetime
import csv
import textwrap
from dotenv import load_dotenv
from ringcentral import SDK
from ringcentral.http.api_exception import ApiException
from urllib.parse import urlencode
from pick import pick 
import logging
from pathlib import Path
load_dotenv()

# Global Variables
DEBUG = os.environ.get('DEBUG', '0').lower() in ('1', 'true', 'yes')
date_stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

# Enable Logging
logging.basicConfig(
	level=logging.DEBUG if DEBUG else logging.INFO,
	format='%(asctime)s [%(levelname)s] %(message)s',
	handlers=[
		logging.StreamHandler(),
		logging.FileHandler("RingCentral_Auditor.log", mode='a')
		]
	)

# RingCentral SDK
rcsdk = SDK( os.environ.get('RC_APP_CLIENT_ID'),
				os.environ.get('RC_APP_CLIENT_SECRET'),
				os.environ.get('RC_SERVER_URL') )
platform = rcsdk.platform()
platform.login( jwt=os.environ.get('RC_JWT_TOKEN') )

# Script housekeeping and disclaimers
def housekeeping():
	wrapped_disclaimer = textwrap.fill(__disclaimer__, width=80)
	wrapped_purpose = textwrap.fill(__purpose__, width=80)
	print(
		f"Author:	{__author__}",
		f"Purpose: {wrapped_purpose}",
		f"Version: {__core_version__}",
		f"Github Link: {__github__}",
		f"Disclaimer: {wrapped_disclaimer}",
		sep='\n'
	)
	print()
	

# Perform requests while staying below API limit. Catch API errors and print error response body.
def connectRequest(url):
	while True:
		try:
			resp = platform.get(url)
			# Set Header variables
			http_status = resp.response().status_code
			headers = resp.response().headers
			api_limit = int(headers.get("X-Rate-Limit-Limit", 1))
			api_limit_remaining = int(headers.get("X-Rate-Limit-Remaining", 1))
			api_limit_window = int(headers.get("X-Rate-Limit-Window", 1))
			# Check API limit on each request, if API limit hits 0, sleep the script for the time reported by API Limit Window.
			if api_limit_remaining == 0:
				logging.warning(f'Rate limit has been hit, waiting for {api_limit_window} seconds, the script will automatically resume.')
				time.sleep(api_limit_window)
				continue
			else:
				return resp

		except ApiException as e:
			api_response = e.api_response()
			status_code = 0
			error_text = str(e)
			error_body = error_text

			if api_response:
				try:
					response = api_response.response()
					if response is not None:
						status_code = response.status_code
						error_body = response.text
				except Exception as parse_error:
					logging.debug(f'Failed to parse API response: {parse_error}')

			# Catch 404 errors returned due to API returned data None
			if status_code == 404:
				logging.info(f'404 Not Found for URL {url}')
				return None
			# Catch Answering Rule errors for elements that don't support the feature. 
			elif "AWR-193" in error_body:
				logging.info(f'HTTP Error 400, AWR-193 Answering Rule not supported')
				return None
			# Catch server 500 errors and sleep for 5 seconds to.
			elif status_code >= 500:
				logging.error(f'Server error {status_code}, retrying after short delay...')
				time.sleep(5)
				continue
			# Catch any unhandled API error.
			else:
				logging.error(f'Unhandled API error ({status_code}) at {url}:{error_body}')
				return None

		except Exception as e:
			logging.critical(f'Non-API Error Occurred {str(e)}')
			sys.exit()

# Performs a connection test to the RingCentral API and returns True if the response is HTTP 200, also retrieves and prints the company info to console.
def connection_test():
	try:
		connect_test_url = connectRequest('/restapi/v2/accounts/~')
		resp_rc_serviceplan = connectRequest('/restapi/v1.0/account/~/service-info')

		if connect_test_url.response().status_code == 200:
			print(f'Connection returned 200 OK, displaying company information.\n')
			print (f'#'*80, '\n\u25BA\u25BA\u25BA Company Information\n','#'*80, sep="")
			
			# Retrieve company info, service plan, billing
			company_info = json.loads(connect_test_url.text())
			rc_serviceplan_info = json.loads(resp_rc_serviceplan.text())
			# Company info
			company_status = company_info.get('status')
			company_name = company_info.get('companyName')
			company_number = company_info.get('mainNumber')
			company_address_street = company_info.get('companyAddress', {}).get('street')
			company_address_city = company_info.get('companyAddress', {}).get('city')
			company_address_state = company_info.get('companyAddress', {}).get('state')
			company_address_zip = company_info.get('companyAddress', {}).get('zip')
			company_address_country = company_info.get('companyAddress', {}).get('country')
			# Billing info
			rc_plan_type = rc_serviceplan_info.get('servicePlan', {}).get('name')
			rc_billing_schedule = rc_serviceplan_info.get('billingPlan', {}).get('durationUnit')
			
			# Print the company information to console
			print (
				f'Company Name - {company_name}',
				f'Company Status - {company_status}',
				f'Company Number - {company_number}',
				f'Company Address - {company_address_street}, {company_address_city}, {company_address_state}, {company_address_zip}, {company_address_country}\n',
				sep='\n'
				)
			print (f'#'*80, '\n\u25BA\u25BA\u25BA Plan and Billing Info\n','#'*80, sep="")
			print (
				f'RingCentral Plan: {rc_plan_type}',
				f'Billing Schedule: {rc_billing_schedule}\n',
				sep='\n'
				)

			# Asks the user to confirm the displayed company info is correct, to ensure users don't run the audit on the wrong account. 
			while True:
				confirmation = input("Please confirm the company information displayed above is correct: (y/n)")
				if confirmation in ['y', 'n']:
					if confirmation == 'y':
						print("Confirmed Company Settings\n")
						break
					else:
						sys.exit ("User selected No for company confirmation. Please check your JWT and client app information provided in .env")
				print ("Please enter 'y' or 'n'.")
			
			# Asks the user to enter a name for the audit, this will be the name of the csv file.
			while True:
				global audit_file_name
				audit_file_name = str(input("Please enter a name for the audit (NOTE: The files are automatically datestamped): "))
				if audit_file_name and audit_file_name.replace(" ", "") != "":
					cleaned_file_name = audit_file_name.replace(" ", "").replace("/", "-")
					audit_file_name = cleaned_file_name
					return True

	except Exception as e:
		print (f'Error during API request: Error \u25BA\u25BA {e}')

def audit_checker (audit_url):
	try:
		resp = connectRequest(audit_url)
		totalElements = resp.json().paging.totalElements
		user_count = totalElements
		print ('#'*80, f'\n\u25BA\u25BA\u25BA Found {totalElements} Users\n', '#'*80, sep="")
		print ()
		
		while True:
			api_filter_info = "You can customise the filter parameters to modify the returned extensions from RingCentral. Note that most elements in RingCentral count as extensions (Users, Message-Only Extensions, Call Queues, IVR Menus, ect). If you select (n) no filter parameter will be applied, returning all extensions in the RingCentral system including the afore mentioned elements. This will result in certain fields returning None."
			wrapped_api_filter_info = textwrap.fill(api_filter_info, width=80)
			print (wrapped_api_filter_info)
			print ()
			ask_audit = str(input("Do you want to customise the API Filter Parameters?(y/n): "))
			if ask_audit in ['y', 'n']:
				break
			print ("Invalid input. Please enter 'y' or 'n'.")

		if ask_audit == "y":
			print("API Filter Parameter custimisation selected...\n")
			time.sleep(1)

			# Load pick menu - Bulk or Individual Selection
			p1_title = 'Are you auditing an entire system or just specific users?'
			p1_query_options = ['System', 'Specific']
			p1_list_option, p1_index = pick(p1_query_options, p1_title, indicator='\u25BA\u25BA')

			if p1_list_option == "System":
				# Jump to audit_checker_system()
				filter_user_count, user_count, built_url  = audit_checker_system(totalElements)
				return (filter_user_count, user_count, built_url)
			
			elif p1_list_option == "Specific":
				# Jump to individual filter options
				filter_user_count, user_count, built_url = audit_checker_specific(totalElements)
				return (filter_user_count, user_count, built_url)
		
		elif ask_audit == "n":
			print("No customisation to the API Filter Parameters selected, proceeding...\n")
			built_url = str(f'/restapi/v1.0/account/~/extension?perPage={totalElements}')
			filter_user_count = False
			return (filter_user_count, user_count, built_url)

	except Exception as e:
		sys.exit(f'Error occured: '+ str(e))

def audit_checker_system(totalElements):
	while True:
		# Load pick menu, Select extension Type, multi-select returns Tuple
		ext_type_title = 'Select (SPACE) what extension type you want to filter for. Press ENTER to continue:'
		extension_types_list = [
		'User',
		'Call Queue',
		'Announcement',
		'Voicemail',
		'IVR Menu',
		'Limited Extensions',
		'Site',
		'Park Locations'
		]
		extension_types= []
		ext_type_options = pick(extension_types_list, ext_type_title, multiselect=True, min_selection_count=1, indicator='\u25BA\u25BA')
		for option, _ in ext_type_options:
			o = option.strip()
			logging.info(f"Checking option: '{o}'")
			if o == 'User':
				extension_types.append("User")
			elif o == 'Call Queue':
				extension_types.append("Department")
				wrapped_disclaimer_call_queue_filter = textwrap.fill("Because you selected Call Queue, an additional csv file will be created with enhanced call queue information.", width=80)
				print(wrapped_disclaimer_call_queue_filter)
				input("Press Enter To continue")
			elif o == 'Announcement':
				extension_types.append("Announcement")
			elif o == 'Voicemail':
				extension_types.append("Voicemail")
			elif o == 'IVR Menu':
				extension_types.append("IvrMenu")
			elif o == 'Limited Extensions':
				extension_types.append("Limited")
			elif o == 'Site':
				extension_types.append("Site")
			elif o == 'Park Locations':
				extension_types.append("ParkLocation")
			else:
				sys.exit(f"Unrecognized option: '{o}'") 

		# Load pick menu, multi-select returns Tuple
		ext_status_title = 'Select (SPACE) what extension type you want to filter for. Press ENTER to continue:'
		extension_status = [
		'Enabled',
		'Disabled',
		'Frozen',
		'Not Activated',
		'Unassigned'
		]
		status_types= []
		ext_status_options = pick(extension_status, ext_status_title, multiselect=True, min_selection_count=1, indicator='\u25BA\u25BA')
		for option, _ in ext_status_options:
			o = option.strip()
			logging.info(f"Checking option: '{o}'")
			if o == 'Enabled':
				status_types.append("Enabled")
			elif o == 'Disabled':
				status_types.append("Disabled")
			elif o == 'Frozen':
				status_types.append("Frozen")
			elif o == 'Not Activated':
				status_types.append("NotActivated")
			elif o == 'Unassigned':
				status_types.append("Unassigned")
			else:
				sys.exit(f"Unrecognized option: '{o}'")
		queryParams = urlencode(
			{
			'type': extension_types,
			'status': status_types
			}, doseq=True)

		built_url = f'/restapi/v1.0/account/~/extension?{queryParams}'
		filter_user_count = connectRequest(built_url).json().paging.totalElements
		filter_user_built_url = str(f'/restapi/v1.0/account/~/extension?perPage={filter_user_count}&{queryParams}')

		if filter_user_count:
			print ('#'*80, f'\nFound {filter_user_count} users with current filter parameters, proceeding to field customisation.\n', '#'*80, sep="")
			print ()
			return (filter_user_count, totalElements, filter_user_built_url) 
		print ("No results returned from filter paramaters. Please review your filter paramaters and try again.\n")
		time.sleep(3)

def audit_checker_specific(totalElements):
	while True:
		# Load pick menu - Bulk or Individual Selection
		s_title = 'You can choose between an Extension Number or Email.'
		s_query_options = ['Extension Number', 'Email']
		s_list_option, s_index = pick(s_query_options, s_title, indicator='\u25BA\u25BA')

		if s_list_option == 'Extension Number':
			while True:
				query_extension = input("Enter the Extension Number: ")
				if query_extension.isdigit():
					break
				print ("Please only enter a numeric extension number!")
			queryParams = urlencode({'extensionNumber': query_extension}, doseq=True)
			built_url = f'/restapi/v1.0/account/~/extension?{queryParams}'
			filter_user_count = connectRequest(built_url).json().paging.totalElements
			filter_user_built_url = str(f'/restapi/v1.0/account/~/extension?perPage={filter_user_count}&{queryParams}')
			
			if filter_user_count:
				print (f'Found {filter_user_count} users with current filter parameters, proceeding to field customisation.\n')
				return (filter_user_count, totalElements, filter_user_built_url) 
			print ("No results returned from filter paramaters. Please review your filter paramaters and try again.\n")
			time.sleep(3)

		elif list_option == 'Email': # need to add seperation via comma, multiple values.
			query_email = input("Enter the Email Address: ")
			queryParams = urlencode({'email': query_email}, doseq=True)
			built_url = f'/restapi/v1.0/account/~/extension?{queryParams}'
			filter_user_count = connectRequest(built_url).json().paging.totalElements
			filter_user_built_url = str(f'/restapi/v1.0/account/~/extension?perPage={filter_user_count}&{queryParams}')
			
			if filter_user_count:
				print ('#'*80, f'\nFound {filter_user_count} users with current filter parameters, proceeding to field customisation.\n', '#'*80, sep="")
				print ()
				return (filter_user_count, totalElements, filter_user_built_url) 
			print ("No results returned from filter paramaters. Please review your filter paramaters and try again.\n")
			time.sleep(3)

# Set what dict keys to export to csv for Audit.py
def prep_user_csv():
	# Initialise field variables to False
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
	) = [False] * 18
	field_advisory_info = "The next window will ask you to select which fields you want to export to CSV. Selecting more fields will increase the time taken to audit each users, as well as increase the chance of hitting API rate limiting. If rate limiting occurs, the script will pause for 60 seconds to allow the limit to reset."
	wrapped_field_info = textwrap.fill(field_advisory_info, width=80)
	print(wrapped_field_info)
	input("Press ENTER key to proceed")
	# Load pick menu, multi-select returns Tuple
	title = 'Select (SPACE) what fields you want to export to csv file. (Multiple Selections Allowed, <Default All> includes all fields.) Press ENTER to continue:'
	field_options = [
	'Default All',
	'ID',
	'Name',
	'Number',
	'Direct Number',
	'Status',
	'Type',
	'Site',
	'Company',
	'Department',
	'Job Title',
	'Email',
	'Administrator Check?',
	'User Assigned Role',
	'Setup Wizard Status',
	'DND State',
	'Business Hours Rule Forwarding',
	'After Hours Rule Forwarding',
	'Device Information'
	]
	options = pick(field_options, title, multiselect=True, min_selection_count=1, indicator='\u25BA\u25BA')
	for option, _ in options:
		o = option.strip()
		logging.info(f"Checking option: '{o}'")
		if o == 'Default All':
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
			) = [True] * 18
		elif o == 'ID':
				csv_field_id = True
		elif o == 'Name':
				csv_field_name = True
		elif o == 'Number':
				csv_field_number = True
		elif o == 'Direct Number':
				csv_field_did = True
		elif o == 'Status':
				csv_field_status = True
		elif o == 'Type':
				csv_field_type = True
		elif o == 'Sub Type':
				csv_field_subType = True
		elif o == 'Site':
				csv_field_site = True
		elif o == 'Company':
				csv_field_company = True
		elif o == 'Department':
				csv_field_department = True
		elif o == 'Job Title':
				csv_field_job_title = True
		elif o == 'Email':
				csv_field_email = True
		elif o == 'Administrator Check?':
				csv_field_admin_check = True
		elif o == 'User Assigned Role':
				csv_field_user_assigned_role = True
		elif o == 'Setup Wizard Status':
				csv_field_setup_wizard_status = True
		elif o == 'DND State':
				csv_field_dnd_state = True
		elif o == 'Business Hours Rule Forwarding':
				csv_field_bhr_fw = True
		elif o == 'After Hours Rule Forwarding':
				csv_field_ahr_fw = True
		elif o == 'Device Information':
				csv_field_device_info = True
		else:
				sys.exit(f"Unrecognized option: '{o}'")

	csv_fields = (
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
		)

	return (csv_fields)

#Builds the csv file
def build_csv(datalist):
	results_dir = Path(__file__).resolve().parent.parent
	folder_name = results_dir / 'AuditResults'
	file_name = f'{str(audit_file_name)}-{date_stamp}'+'.csv'

	if not os.path.exists(folder_name):
		os.makedirs(folder_name)
	file_path = os.path.join(folder_name, file_name)

	if os.path.exists(file_path):
		increment_file_name = file_name.replace(".csv", f"_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
		file_name = increment_file_name

	if not datalist:
		print ("No data in dictionary to write")
		return

	fieldnames = list(datalist[0].keys())
	with open(file_path, "w", newline='', encoding="utf-8") as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
		writer.writeheader()
		for row in datalist:
			writer.writerow(row)

#Builds the call queue csv file
def cq_build_csv(datalist):
	results_dir = Path(__file__).resolve().parent.parent
	folder_name = results_dir / 'AuditResults'
	file_name = f'{str(audit_file_name)}-CallQueueDetails-{date_stamp}'+'.csv'
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)
	file_path = os.path.join(folder_name, file_name)

	if os.path.exists(file_path):
		increment_file_name = file_name.replace(".csv", f"_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
		file_name = increment_file_name

	if not datalist:
		print ("No data in call queue dictionary to write")
		return

	fieldnames = list(datalist[0].keys())
	with open(file_path, "w", newline='', encoding="utf-8") as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
		writer.writeheader()
		for row in datalist:
			writer.writerow(row)