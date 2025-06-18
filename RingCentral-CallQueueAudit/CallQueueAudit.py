#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to collect information on the RingCentral instance, useful for conducting audits and health checks on RingCentral instances.
Version:  0.4
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
datalist = []
retry_limit = 6
retry_attempts = 0
start_time = datetime.datetime.now()

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

# Start main thread, checks API connectivity and proceeds if 200 OK is returned.  #
def main():
  print (f'Script Start Time: {start_time}')
  connect_test = connectRequest('/restapi/v2/accounts/~')

  if connect_test.response().status_code == 200:
    print("Connection returned 200 OK, proceeding with audit...")
    #get_ringcentral_callqueue()
    check_ringcentral_callqueue_count()
  else:
    sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")

  end_time = datetime.datetime.now()
  runtime = (end_time - start_time).total_seconds()
  m, s  = divmod(runtime, 60)

  print("Script has completed, audit results:")
  print(f'\nScript End Time:    {end_time}')
  print("Script runtime was: {} minutes and {} seconds".format(int(m), int(s)))
  exit (0)

# Check how many call queues exist, prompts user for constrained audit count.
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue List
def check_ringcentral_callqueue_count ():
  call_queue_count_list = []

  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues')
    call_queue_count_list = len(resp.json().records)
    print (f'Found {call_queue_count_list} Call Queues\nIf you want to restrict the scope of the audit to only a certain amount of call queues, enter the amount now, otherwise press enter.')
    audit_limit = input()

    if audit_limit:
      print(f'Proceeding with audit within the defined constrainst of {audit_limit} call queues.\n')
      get_ringcentral_callqueue(int(audit_limit))
    else:
      print("Audit limit not set, proceeding with full call queue audit.")
      get_ringcentral_callqueue(audit_limit)

  except Exception as e:
    sys.exit("error occured:" + str(e))

# Request the call queues and pass call queue id, name to get_ringcentral_callqueue_members(), if call queue audit constrainst have been set, only audit that many call queues
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue List
def get_ringcentral_callqueue(audit_limit):
  call_queue_count_list = []

  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues')
    if audit_limit:
      print ("Constrained Audit")
      audit_count = 0
      #while audit_count < audit_limit:
      for record in resp.json().records:
        if audit_count == audit_limit:
          print (audit_count)
          break

        else:
          call_queue_count_list.append(record.id)
          call_queue_count = len(call_queue_count_list)
          print (f'\n \u25BA\u25BA\u25BA Call Queues Found: {call_queue_count}\n')
          print (f'{record.name} - {record.extensionNumber}')
          cq_name = (record.name)
          cq_extension = (record.extensionNumber)
          audit_count += 1
          get_ringcentral_callqueue_members(record.id,cq_name,cq_extension)

    else:
      print ("Full Audit")
      for record in resp.json().records:
        call_queue_count_list.append(record.id)
        call_queue_count = len(call_queue_count_list)
        print (f'\n \u25BA\u25BA\u25BA Call Queues Found: {call_queue_count}\n')
        print (f'{record.name} - {record.extensionNumber}')
        cq_name = (record.name)
        cq_extension = (record.extensionNumber)
        get_ringcentral_callqueue_members(record.id,cq_name,cq_extension)

  except Exception as e:
    sys.exit("error occured: " + str(e))


# Iterate through call queues and get member IDs, pass to get_ringcentral_users()
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue Members
def get_ringcentral_callqueue_members(id,cq_name,cq_extension):

  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues/'+str(id)+'/members')

    for record in resp.json().records:
      cq_member_ext = (record.extensionNumber)
      get_ringcentral_users(record.id,cq_name,cq_member_ext,cq_extension)

  except Exception as e:
    sys.exit("error occured: " + str(e))

# Request extension details and pass Call Queue Name, Extension Name, and Extension Number to build_datalist()
# API Reference -> https://developers.ringcentral.com/api-reference/Extensions/listExtensions
def get_ringcentral_users(id,cq_name,cq_member_ext,cq_extension):

  try:
    resp = connectRequest('/restapi/v1.0/account/~/extension/'+str(id))
    cq_member = (resp.json().name)
    print(f'\u2192{resp.json().name} - {cq_member_ext}')
    build_datalist(cq_name,cq_extension,cq_member,cq_member_ext)

  except Exception as e:
    sys.exit(e)

# Uses the collected call queue information to build a dictionary.
def build_datalist(cq_name,cq_extension,cq_member,cq_member_ext):

  datalist.append({
    "Call Queue Name":      cq_name,
    "Call Queue Extension": cq_extension,
    "Call Queue Member":    cq_member,
    "Member Extension":     cq_member_ext
  })
  build_csv(datalist)

# Builds the csv file, sets headers. 
def build_csv(datalist):
    datalist_jsondump = json.dumps(datalist)
    datalist_json = json.loads(datalist_jsondump)
    with open("callQueues.csv", "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=datalist_json[0].keys())
        writer.writeheader()
        for row in datalist_json:
          #print (row['Call Queue Name'], row['Call Queue Extension'], row['Call Queue Member'], row['Member Extension'])
          writer.writerow(row)

# Start Execution
main()
