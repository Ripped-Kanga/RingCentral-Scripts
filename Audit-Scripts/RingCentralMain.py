#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to collect information on the RingCentral instance, useful for conducting audits and health checks on RingCentral instances.
Version:  0.5
Github:   https://github.com/Ripped-Kanga/RingCentral-Scripts
"""
# Import libraries
import os
import sys
import json
import time
import datetime
import csv
from dotenv import load_dotenv
from ringcentral import SDK
import inspect
from pick import pick
load_dotenv()

# Global Variables
retry_limit = 6
retry_attempts = 0

# RingCentral SDK
rcsdk = SDK( os.environ.get('RC_APP_CLIENT_ID'),
        os.environ.get('RC_APP_CLIENT_SECRET'),
        os.environ.get('RC_SERVER_URL') )
platform = rcsdk.platform()
platform.login( jwt=os.environ.get('RC_JWT_TOKEN') )


# Perform requests while staying below API limit. Exit script if retry_limit hits 5. 
def connectRequest(url):
  for connectAttempt in range(retry_limit):
    resp = platform.get(url)

    # Set Header variables
    http_status = resp.response().status_code
    headers = resp.response().headers
    api_limit = int(headers["X-Rate-Limit-Limit"])
    api_limit_remaining = int(headers["X-Rate-Limit-Remaining"])
    #for debugging
    #print (api_limit_remaining)
    api_limit_window = int(headers["X-Rate-Limit-Window"])

    if not http_status == 200:
      print (f'Rate limiting has been applied, waiting for {api_limit_window} seconds, number of retries left is {retry_limit - retry_attempts}')
      retry_attempts =+ 1
      time.sleep(api_limit_window)
      continue

    elif api_limit_remaining == 0:
      retry_after = api_limit_window
      print(f'Rate limit has been hit, waiting for {retry_after} seconds')
      time.sleep(retry_after)
      continue
    
    else:
      return resp

  raise Exception(f"Rate limiting has been hit {retry_limit} times, exiting.")


# Performs a connection test to the RingCentral API and returns True if the response is HTTP 200. 
def connection_test():
  connect_test_url = connectRequest('/restapi/v2/accounts/~')

  if connect_test_url.response().status_code == 200:
    print("Connection returned 200 OK, proceeding with audit...")
    # Retrieve company info
    company_info = connectRequest('/restapi/v2/accounts/~')
    print (f'Company Name - {company_info.json().companyName}\nCompany Number - {company_info.json().mainNumber}\n')
    return True
  else:
    sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")


def audit_checker (audit_url):
  try:
    resp = connectRequest(audit_url)
    totalElements = resp.json().paging.totalElements
    calling_function = inspect.stack()[1][3]

    if calling_function == "main_user":
      print (f'Found {totalElements} Users:\n')
      ask_audit = str(input("Do you want to customise the conditions of the audit?(y/n: "))

      if ask_audit.lower() == "y":
        print("Customised audit selected.")
        # load pick menu
        title = 'Select a query option below: (You can only choose one!)'
        query_options = ['extensionNumber', 'email', 'status']
        option, index = pick(query_options, title, indicator='>>')

        match option:
          case 'extensionNumber':
            query_extension = int(input("Enter the Extension Number: "))
            query_option = str(f"{option}="+str(query_extension))
          case 'email':
            query_email = (input("Enter the Email Address: "))
            query_option = (f'{option}='+query_email)
          case 'status':
            query_status = str(input("Enter the User Status (Enabled, Disabled, NotActivated, Unassigned: "))
            query_option = str(f"{option}="+query_status.capitalize())
          case _:
            sys.exit("An error occured in the pick list.")


        built_url = str(f'/restapi/v1.0/account/~/extension?perPage={totalElements}&{query_option}')
        return (totalElements, built_url)

      elif ask_audit.lower() == "n":
        print("No customisation will apply to the user audit, proceeding.")
        built_url = str(f'/restapi/v1.0/account/~/extension?perPage={totalElements}')
        return (totalElements, built_url)

    elif calling_function == "main_callqueue":
      print (f'Found {totalElements} Call Queues:\nIf you want to restrict the scope of the audit to only a certain amount of call queues, enter the amount now, otherwise press enter.')
    audit_limit_input = input()

    if audit_limit_input:
      print(f'Proceeding with audit within the defined constrainst of {audit_limit_input} call queues.\n')
      return (int(audit_limit_input),totalElements)

    else:
      print("Audit limit not set, proceeding with full call queue audit.")
      return (audit_limit_input,totalElements)

  except Exception as e:
    sys.exit("error occured:" + str(e))
