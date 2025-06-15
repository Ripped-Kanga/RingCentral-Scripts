#!/usr/bin/python

'''
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to collect information on the RingCentral instance, useful for conducting audits and health checks on RingCentral instances.
Version:  0.3
Github:   https://github.com/Ripped-Kanga/RingCentral-Scripts
'''


# Import libraries
import os
import sys
import json
import time
from dotenv import load_dotenv
from ringcentral import SDK
load_dotenv()

# RingCentral SDK
rcsdk = SDK( os.environ.get('RC_APP_CLIENT_ID'),
        os.environ.get('RC_APP_CLIENT_SECRET'),
        os.environ.get('RC_SERVER_URL') )
platform = rcsdk.platform()
platform.login( jwt=os.environ.get('RC_USER_JWT') )

# Perform requests while staying below API limit. Exit script if retry_limit hits 5. 

def connectRequest(url, retry_limit=1):
  for connectAttempt in range(retry_limit):
    resp = platform.get(url)

    # Set Header variables
    http_status = resp.response().status_code
    headers = resp.response().headers
    api_limit = int(headers["X-Rate-Limit-Limit"])
    api_limit_remaining = int(headers["X-Rate-Limit-Remaining"])
    #print ("Remaining requests - ",remaining)
    api_limit_window = int(headers["X-Rate-Limit-Window"])

    if api_limit_remaining == 0:
      retry_after = api_limit_window
      print(f'Rate limit has been hit, waiting for {retry_after} seconds')
      time.sleep(retry_after)
      continue

    if resp.ok:
      return resp

  raise Exception(f"[!] Failed after {retry_limit} attempts: {url}")

# Request the call queues and prints the call queue name, pass call queue ID to get_RC_CQM
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue List
def get_RC_CQ():
  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues')
    for record in resp.json().records:
      print(f'### Call Queue ###\n{record.name}\nMembers are:')
      get_RC_CQM(record.id)
      print (f'\n')
  except Exception as e:
    print (e)

# Iterate through call queues and get member IDs, pass to get_RC_Users
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue Members
def get_RC_CQM(id):
    try:
      #resp = platform.get ('/restapi/v1.0/account/325629124/call-queues/'+str(id)+'/members')
      resp = connectRequest('/restapi/v1.0/account/~/call-queues/'+str(id)+'/members')
      for record in resp.json().records:
        get_RC_Users(record.id, record.extensionNumber)
    except Exception as e:
            print (e)

# Print call queue members names to console
# API Reference -> https://developers.ringcentral.com/api-reference/Extensions/listExtensions
def get_RC_Users(id, extensionNumber):
  try:
    resp = connectRequest('/restapi/v1.0/account/~/extension/'+str(id))
    print (f'{resp.json().name} - {extensionNumber}')

  except Exception as e:
    print (e)

# Start Execution
get_RC_CQ()