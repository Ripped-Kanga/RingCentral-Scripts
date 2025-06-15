#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to collect information on the RingCentral instance, useful for conducting audits and health checks on RingCentral instances.
Version:  0.3
Github:   https://github.com/Ripped-Kanga/RingCentral-Scripts
"""
# Import libraries
import os
import sys
import json
import time
import csv
from dotenv import load_dotenv
from ringcentral import SDK
load_dotenv()

# Global Variables
datalist = []
retry_limit = 6
retry_attempts = 0
# RingCentral SDK
rcsdk = SDK( os.environ.get('RC_APP_CLIENT_ID'),
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
    #print ("Remaining requests - ",remaining)
    api_limit_window = int(headers["X-Rate-Limit-Window"])

    if http_status == 429:
      print (f'Rate limiting has been applied, waiting for {api_limit_window} seconds, number of retries left is {retry_limit - retry_attempts}')
      retry_attempts =+ 1
      time.sleep(api_limit_window)
      continue

    elif api_limit_remaining == 0:
      retry_after = api_limit_window
      print(f'Rate limit has been hit, waiting for {retry_after} seconds')
      time.sleep(retry_after)
      continue
    
    else: #resp.ok:
      return resp

  raise Exception(f"Rate limiting has been hit {retry_limit} times, exiting.")

# Start main thread #
def main():
  start_time = time.time()
  cq_count = 0
  cqm_count = 0

  #perform credential check by checking if a 200 is returned from API
  connect_test = connectRequest('/restapi/v2/accounts/~')
  if connect_test.response().status_code == 200:
    print("Credentials good, proceeding with audit...")
    get_ringcentral_callqueue()
  else:
    sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")

# Request the call queues and prints the call queue name, pass call queue ID to get_ringcentral_callqueue_members
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue List
def get_ringcentral_callqueue():
  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues')
    for record in resp.json().records:
      cq_name = (record.name)
      get_ringcentral_callqueue_members(record.id,cq_name)
  except Exception as e:
    sys.exit("error occured: " + str(e))

# Iterate through call queues and get member IDs, pass to get_ringcentral_users
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue Members
def get_ringcentral_callqueue_members(id,cq_name):
  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues/'+str(id)+'/members')
    for record in resp.json().records:
      cq_member_ext = (record.extensionNumber)
      get_ringcentral_users(record.id, record.extensionNumber, cq_name, cq_member_ext)

  except Exception as e:
    sys.exit("error occured: " + str(e))

# Print call queue members names to console
# API Reference -> https://developers.ringcentral.com/api-reference/Extensions/listExtensions
def get_ringcentral_users(id, extensionNumber,cq_name,cq_member_ext):
  try:
    resp = connectRequest('/restapi/v1.0/account/~/extension/'+str(id))
    cq_member = (resp.json().name)
    build_datalist(cq_name,cq_member,cq_member_ext)
  except Exception as e:
    sys.exit(e)

def build_datalist(cq_name, cq_member, cq_member_ext):
  datalist.append({
    "Call Queue Name": cq_name,
    "Call Queue Member": cq_member,
    "Member Extension": cq_member_ext
  })
  build_csv(datalist)

def build_csv(datalist):
    datalist_jsondump = json.dumps(datalist)
    datalist_json = json.loads(datalist_jsondump)

    titles=('Call Queue Names', 'Call Queue Members', 'Member Extension')
    with open("callQueues.csv", "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=datalist_json[0].keys())
        writer.writeheader()
        for row in datalist_json:
            print (row['Call Queue Name'], row['Call Queue Member'], row['Member Extension'])
            writer.writerow(row)

# Start Execution
main()
