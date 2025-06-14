#!/usr/bin/python

# You get the environment parameters from your
# application dashbord in your developer account
# https://developers.ringcentral.com

import os
import sys
import json
#import requests
import time
#from requests import Response
from dotenv import load_dotenv
from ringcentral import SDK
load_dotenv()

"""
# RingCentral authentication info, populate this in your .env file
rcsdk = SDK( os.environ.get('RC_APP_CLIENT_ID'),
             os.environ.get('RC_APP_CLIENT_SECRET'),
             os.environ.get('RC_SERVER_URL') )
platform = rcsdk.platform()
try:
  platform.login( jwt=os.environ.get('RC_USER_JWT') )
except Exception as e:
  sys.exit("Unable to authenticate to platform: " + str(e))
"""
rcsdk = SDK( os.environ.get('RC_APP_CLIENT_ID'),
        os.environ.get('RC_APP_CLIENT_SECRET'),
        os.environ.get('RC_SERVER_URL') )
platform = rcsdk.platform()
platform.login( jwt=os.environ.get('RC_USER_JWT') )
def connectRequest(url, retry_limit=3):
  
  for loginAttempt in range(retry_limit):
    resp = platform.get(url)
    # Set Header variables
    headers = resp.response().headers
    limit = int(headers["X-Rate-Limit-Limit"])
    remaining = int(headers["X-Rate-Limit-Remaining"])
    #print ("Remaining requests - ",remaining)
    window = int(headers["X-Rate-Limit-Window"])
    if remaining == 2:
      retry_after = window
      print(f'Rate Limit has been hit, waiting for {retry_after} seconds')
      time.sleep(retry_after)
      continue

    if resp.ok:
      return resp

  raise (f"Failed")

# Request the call queues and prints the call queue name, pass call queue ID to get_RC_CQM
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue List
def get_RC_CQ():
    try:
      #resp = platform.get('/restapi/v1.0/account/~/call-queues')
      resp = connectRequest('/restapi/v1.0/account/~/call-queues')
      for callQueueList in resp.json().records:
        print(f'### Call Queue ###\n{callQueueList.name}\nMembers are:')
        get_RC_CQM(callQueueList.id)
        print (f'\n')
    except Exception as e:
      print (e)

# Iterate through call queues and get member IDs, pass to get_RC_Users
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue Members
def get_RC_CQM(id):
    try:
      #resp = platform.get ('/restapi/v1.0/account/325629124/call-queues/'+str(id)+'/members')
      resp = connectRequest('/restapi/v1.0/account/~/call-queues/'+str(id)+'/members')
      for cqMembers in resp.json().records:
        #print(f'Member IDs {cqMembers.id}')
        get_RC_Users(cqMembers.id, cqMembers.extensionNumber)
    except Exception as e:
            print (e)

# Print call queue members names to console
# API Reference -> https://developers.ringcentral.com/api-reference/Extensions/listExtensions
def get_RC_Users(id, extensionNumber):
    try:
      #resp = platform.get ('/restapi/v1.0/account/~/extension/'+str(id))
      resp = connectRequest('/restapi/v1.0/account/~/extension/'+str(id))
      print (f'{resp.json().name} - {extensionNumber}')

    except Exception as e:
        print (e)
# Start Execution
get_RC_CQ()