#!/usr/bin/python

__author__ = "Alan Saunders"
__purpose__ = "Uses the RingCentral API to collect information on the RingCentral instance, useful for conducting audits and health checks on RingCentral instances."
__core_version__ = "0.95 - alpha 2"
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
import inspect #Used for tracing stack
from pick import pick #Pick Menu
load_dotenv()

# Global Variables
DEBUG = False


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
			api_limit = int(headers["X-Rate-Limit-Limit"])
			api_limit_remaining = int(headers["X-Rate-Limit-Remaining"])
			api_limit_window = int(headers["X-Rate-Limit-Window"])
			# Check API limit on each request, if API limit hits 0, sleep the script for the time reported by API Limit Window.
			if api_limit_remaining == 0:
				retry_after = api_limit_window
				print(f'Rate limit has been hit, waiting for {retry_after} seconds, the script will automatically resume.')
				time.sleep(retry_after)
				continue
			else:
				return resp

		except Exception as e:
			error_message = str(e)

			if "HTTP 404" in error_message:
				if DEBUG == True:
					print(f'404 Not Found for URL: {url}')
					return None
				else:
					return None
					
			else:
				print(f'Unexpected API error for URL {url}:\n{error_message}')
				return None


# Performs a connection test to the RingCentral API and returns True if the response is HTTP 200, also retrieves and prints the company info to console.
def connection_test():
	try:
		connect_test_url = connectRequest('/restapi/v2/accounts/~')
		resp_rc_serviceplan = connectRequest('/restapi/v1.0/account/~/service-info')

		if connect_test_url.response().status_code == 200:
			print(f'Connection returned 200 OK, displaying company information.\n')
			print (f'#'*27, '\n### Company Information ###\n','#'*27, sep="")
			
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
			print (f'#'*29, '\n### Plan and Billing Info ###\n','#'*29, sep="")
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
						return True
					else:
						sys.exit ("User selected No for company confirmation. Please check your JWT and client app information provided in .env")
				print ("Please enter 'y' or 'n'.")
		
	except Exception as e:
		print (f'Error during API request: Error \u25BA\u25BA {e}')


def audit_checker (audit_url):
	try:
		resp = connectRequest(audit_url)
		totalElements = resp.json().paging.totalElements
		calling_function = inspect.stack()[1][3]

		#Invoked if the calling script is UserAudit.py
		if calling_function == "main_user":
			print (f'Found {totalElements} Users:\n')
			
			while True:
				ask_audit = str(input("Do you want to customise the API Filter Parameters?(y/n: "))
				if ask_audit in ['y', 'n']:
					break
				print("Invalid input. Please enter 'y' or 'n'.")

			if ask_audit == "y":
				print("API Filter Parameter custimisation selected...\n")
				time.sleep(3)
				# Load pick menu
				title = 'Select a query option below: (You can only choose one!)'
				query_options = ['extensionNumber', 'email', 'status']
				option, index = pick(query_options, title, indicator='\u25BA\u25BA')
				
				while True:
					match option:
						case 'extensionNumber':
							while True:
								query_extension = input("Enter the Extension Number: ")
								if query_extension.isdigit():
									break
								print ("Please only enter a numeric extension number!")
							query_option = str(f"{option}="+str(query_extension))
						case 'email':
							query_email = input("Enter the Email Address: ")
							query_option = (f'{option}='+query_email)
						case 'status':
							while True:
								query_status = str(input("Enter the User Status (Enabled, Disabled, NotActivated, Unassigned: "))
								if query_status in ['Enabled', 'Disabled', 'NotActivated', 'Unassigned']:
									break
								print ("Invalid input, please review the options and try again.\n")
							query_option = str(f'{option}='+query_status)
						case _:
							sys.exit("An error occured in the pick list.")

					built_url = str(f'/restapi/v1.0/account/~/extension?perPage={totalElements}&type=User&{query_option}')
					filter_user_count = connectRequest(built_url).json().paging.totalElements
					filter_user_built_url = str(f'/restapi/v1.0/account/~/extension?perPage={filter_user_count}&type=User&{query_option}')
					
					if filter_user_count:
						print (f'Found {filter_user_count} users with current filter parameters, proceeding to field customisation.\n')
						return (filter_user_count, totalElements, filter_user_built_url) 
					print ("No results returned from filter paramaters. Please review your filter paramaters and try again.\n")

			elif ask_audit == "n":
				print("No customisation to the API Filter Parameters selected, proceeding...\n")
				built_url = str(f'/restapi/v1.0/account/~/extension?perPage={totalElements}&type=User')
				filter_user_count = False
				return (filter_user_count, totalElements, built_url)


		#Invoked if the calling script is CallQueueAudit.py
		elif calling_function == "main_callqueue":
			print (f'Found {totalElements} Call Queues:\n')
			while True:
				audit_limit_input = input(f'If you want to restrict the scope of the audit to only a certain amount of call queues, enter the amount now, otherwise press enter:')
				if audit_limit_input == "":
					print("Audit limit not set, proceeding with full call queue audit.")
					return (audit_limit_input,totalElements)
				elif audit_limit_input.isdigit():
					print(f'Proceeding with audit within the defined constrainst of {audit_limit_input} call queues.\n')
					return (int(audit_limit_input),totalElements)
				else:
					print ("\nInvalid input. Please enter the number of call queues to audit, or to audit all just press enter.")

		# Invoked if the calling script is PhoneNumberAudit.py
		elif calling_function == "main_phone_number_audit":
			print (f'Found {totalElements} Phone Numbers:\n')
			
			while True:
				ask_audit = str(input("Do you want to customise the API Filter Parameters?(y/n: "))
				if ask_audit in ['y', 'n']:
					break
				print("Invalid input. Please enter 'y' or 'n'.")
			
			if ask_audit == 'y':
				# Load pick menu
				title = 'Select a query option below: (You can only choose one!)'
				query_options = ['CompanyNumber', 'PhoneLine', 'DirectNumber', 'Inventory']
				option, index = pick(query_options, title, indicator='\u25BA\u25BA')
				match option:
					case 'CompanyNumber':
						query_option = option
					case 'DirectNumber':
						query_option = option
					case 'Inventory':
						query_option = option
					case 'PhoneLine':
						query_option = option
					case _:
						sys.exit("An error occured in the pick list.")

				built_url = str(f'/restapi/v2/accounts/~/phone-numbers?usageType={query_option}')
				filtered_phone_number_count = connectRequest(built_url).json().paging.totalElements
				filtered_phone_number_built_url = str(f'/restapi/v2/accounts/~/phone-numbers?usageType={query_option}')
				return (filtered_phone_number_count, totalElements, filtered_phone_number_built_url)

			elif ask_audit == 'n':
				print ("No customisation to the API Filter Parameters selected, proceeding...")
				built_url = f'/restapi/v2/accounts/~/phone-numbers?perPage={totalElements}'
				filtered_phone_number_count = False
				return (filtered_phone_number_count, totalElements, built_url)
	
	except Exception as e:
		sys.exit(f'Error occured: '+ str(e))

# Set what dict keys to export to csv for UserAudit.py
def prep_user_csv():
	# Initialise field variables to False
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
	'Status',
	'Type',
	'Sub Type',
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
		print(f"Checking option: '{o}'")
		if o == 'Default All':
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
			) = [True] * 18
		elif o == 'ID':
				csv_field_id = True
		elif o == 'Name':
				csv_field_name = True
		elif o == 'Number':
				csv_field_number = True
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
		)

	return (csv_fields)
