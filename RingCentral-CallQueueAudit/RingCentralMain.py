#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to collect information on the RingCentral instance, parses it back to the calling function.
Version:  0.2
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
load_dotenv()

# Global Variables
retry_limit = 6
retry_attempts = 0

# RingCentral SDK
rcsdk = SDK(  os.environ.get('RC_APP_CLIENT_ID'),
              os.environ.get('RC_APP_CLIENT_SECRET'),
              os.environ.get('RC_SERVER_URL') )
platform = rcsdk.platform()
platform.login( jwt=os.environ.get('RC_USER_JWT') )

# Perform requests while staying below API limit. Exit script if retry_limit hits 5. 
def connectRequest(url):
  for connectAttempt in range(retry_limit):
    resp = platform.get(url)

    # Set Header variables
    http_status = resp.response().status_code
    headers = resp.response().headers
    api_limit = int(headers["X-Rate-Limit-Limit"])
    api_limit_remaining = int(headers["X-Rate-Limit-Remaining"])
    api_limit_window = int(headers["X-Rate-Limit-Window"])

    if not http_status == 200:
      print (f'Rate limiting or another error has occured, waiting for {api_limit_window} seconds, number of retries left is {retry_limit - retry_attempts}')
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

# Check how many call queues exist, prompts user for constrained audit count, and passes back to main()
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue List
def callqueue_audit_limit ():
  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues')
    call_queue_count_list = len(resp.json().records)
    print (f'Found {call_queue_count_list} Call Queues:\nIf you want to restrict the scope of the audit to only a certain amount of call queues, enter the amount now, otherwise press enter.')
    audit_limit_input = input()

    if audit_limit_input:
      print(f'Proceeding with audit within the defined constrainst of {audit_limit_input} call queues.\n')
      return (int(audit_limit_input),call_queue_count_list)
    else:
      print("Audit limit not set, proceeding with full call queue audit.")
      return (audit_limit_input,call_queue_count_list)

  except Exception as e:
    sys.exit("error occured:" + str(e))