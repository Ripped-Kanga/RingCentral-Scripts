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
from RingCentralMain import connectRequest, callqueue_audit_limit

# Global Variables
datalist = []
start_time = datetime.datetime.now()



# Start main thread, checks API connectivity and proceeds if 200 OK is returned.  #
def main():
  print (f'Script Start Time: {start_time}')
  connect_test = connectRequest('/restapi/v2/accounts/~')

  if connect_test.response().status_code == 200:
    print("Connection returned 200 OK, proceeding with audit...")
    audit_limit, call_queue_count = callqueue_audit_limit()
    get_ringcentral_callqueue(audit_limit)
  else:
    sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")

  end_time = datetime.datetime.now()
  runtime = (end_time - start_time).total_seconds()
  m, s  = divmod(runtime, 60)

  print("Script has completed, audit results:")
  if audit_limit:
    print(f'{call_queue_count} call queues found, but only {audit_limit} audited.')
  else:
    print(f'{call_queue_count} call queues found and audited.')
  print(f'\nScript End Time:    {end_time}')
  print("Script runtime was: {} minutes and {} seconds".format(int(m), int(s)))
  exit (0)

# Request the call queues and parse call queue id, name to get_ringcentral_callqueue_members(), if call queue audit constrainst have been set, only audit that many call queues
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue List
def get_ringcentral_callqueue(audit_limit):
  call_queue_count_list = []

  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues')
    if audit_limit:
      print ("Constrained Audit")
      audit_count = 0
      for record in resp.json().records:
        if audit_count == audit_limit:
          break

        else:
          call_queue_count_list.append(record.id)
          call_queue_count = len(call_queue_count_list)
          print (f'\n \u25BA\u25BA\u25BA Call Queues Found: {call_queue_count}\n')
          print (f'({record.name} - {record.extensionNumber})')
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


# Iterate through call queues and get member IDs, parse to get_ringcentral_users()
# API Reference -> https://developers.ringcentral.com/guide/voice/call-routing/manual/call-queues ## Read Call Queue Members
def get_ringcentral_callqueue_members(id,cq_name,cq_extension):

  try:
    resp = connectRequest('/restapi/v1.0/account/~/call-queues/'+str(id)+'/members')

    for record in resp.json().records:
      cq_member_ext = (record.extensionNumber)
      get_ringcentral_users(record.id,cq_name,cq_member_ext,cq_extension)

  except Exception as e:
    sys.exit("error occured: " + str(e))

# Request extension details and parse Call Queue Name, Extension Name, and Extension Number to build_datalist()
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
          #enable below print for debugging
          #print (row['Call Queue Name'], row['Call Queue Extension'], row['Call Queue Member'], row['Member Extension'])
          writer.writerow(row)

# Start Execution
if __name__ == "__main__":
    main()
