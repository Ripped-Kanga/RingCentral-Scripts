#!/usr/bin/python

__author__ = "Alan Saunders"
__purpose__ = "Uses the RingCentral API to collect information on the RingCentral instance, useful for conducting audits and health checks on RingCentral instances."
__core_version__ = "0.7"
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
#from ringcentral.http.api_exception import ApiException
from ringcentral import SDK#, http
import inspect #Used for tracing stack
from pick import pick
load_dotenv()

# Global Variables

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
		f"Author: {__author__}",
		f"Purpose: {wrapped_purpose}",
		f"Version: {__core_version__}",
		f"Github Link: {__github__}",
		f"Disclaimer: {wrapped_disclaimer}",
		sep='\n'
	)
	print()
	

# Perform requests while staying below API limit.
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
			if api_limit_remaining == 0:
				retry_after = api_limit_window
				print(f'Rate limit has been hit, waiting for {retry_after} seconds, the script will automatically resume.')
				time.sleep(retry_after)
				continue
				
			else:
				return resp
		except Exception as e:
			print (f'Error during API request: Error \u25BA\u25BA {e}')

# Performs a connection test to the RingCentral API and returns True if the response is HTTP 200, also retrieves and prints the company info.
def connection_test():
	connect_test_url = connectRequest('/restapi/v2/accounts/~')
	resp_rc_serviceplan = connectRequest('/restapi/v1.0/account/~/service-info')

	if connect_test_url.response().status_code == 200:
		print(f'Connection returned 200 OK, displaying company information.\n')
		print (f'#'*27, '\n### Company Information ###\n','#'*27, sep="")
		
		# Retrieve company info, service plan, billing
		company_info = json.loads(connect_test_url.text())
		rc_serviceplan_info = json.loads(resp_rc_serviceplan.text())
		rc_plan_type = rc_serviceplan_info.get('servicePlan', {}).get('name')
		rc_billing = rc_serviceplan_info.get('billingPlan', {}).get('durationUnit')
		
		# Print the company information to console
		print (f'Company Name - {company_info.get('companyName')}\nCompany Number - {company_info.get('mainNumber')}\n')
		print (f'#'*29, '\n### Plan and Billing Info ###\n','#'*29, sep="")
		print (f'RingCentral Plan: {rc_plan_type}\nBilling Schedule: {rc_billing}\n')
		while True:
			confirmation = input("Please confirm the company information displayed above is correct: (y/n)")
			if confirmation in ['y', 'n']:
				if confirmation == 'y':
					return True
				else:
					sys.exit ("User selected No for company confirmation. Please check your JWT and client app information provided in .env")
			print ("Please enter 'y' or 'n'.")
		
	else:
		sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")


def audit_checker (audit_url):
	try:
		resp = connectRequest(audit_url)
		totalElements = resp.json().paging.totalElements
		calling_function = inspect.stack()[1][3]

		#Invoked if the calling script is UserAudit.py
		if calling_function == "main_user":
			print (f'Found {totalElements} Users:\n')
			
			while True:
				ask_audit = str(input("Do you want to customise the conditions of the audit?(y/n: "))
				if ask_audit in ['y', 'n']:
					break
				print("Invalid input. Please enter 'y' or 'n'.")

			if ask_audit == "y":
				print("Customised audit selected.")
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
								print ("Invalid input, please review the options and try again.")
							query_option = str(f'{option}='+query_status)
						case _:
							sys.exit("An error occured in the pick list.")

					built_url = str(f'/restapi/v1.0/account/~/extension?perPage={totalElements}&type=User&{query_option}')
					filter_user_count = connectRequest(built_url).json().paging.totalElements
					filter_user_built_url = str(f'/restapi/v1.0/account/~/extension?perPage={filter_user_count}&type=User&{query_option}')
					
					if filter_user_count:
						print (f'Found {filter_user_count} users with current filter parameters, starting audit.')
						return (filter_user_count, totalElements, filter_user_built_url) 
					print ("No results returned from filter paramaters. Please review your filter paramaters and try again.")

			elif ask_audit == "n":
				print("No customisation will apply to the user audit, proceeding.")
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
				ask_audit = str(input("Do you want to customise the conditions of the audit?(y/n: "))
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
				print ("Proceeding with full Phone Number audit...")
				built_url = f'/restapi/v2/accounts/~/phone-numbers?perPage={totalElements}'
				filtered_phone_number_count = False
				return (filtered_phone_number_count, totalElements, built_url)

	except Exception as e:
		sys.exit(f'Error occured: '+ str(e))
