#!/usr/bin/python
"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to collect information on the RingCentral Call Queues.
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
from RingCentralMain import connection_test, connectRequest, audit_checker
import pprint

# Global Variables
call_queue_datalist = []
start_time = datetime.datetime.now()


# Start main thread
def main_callqueue():
	print (f'Script Start Time: {start_time}')
	connection_attempt = connection_test()
	if connection_attempt:
		audit_limit, call_queue_count = audit_checker('/restapi/v1.0/account/~/call-queues')
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


# Request extension details and parse Call Queue Name, Extension Name, and Extension Number to build_datalist()
# API Reference -> https://developers.ringcentral.com/api-reference/Extensions/listExtensions
def get_ringcentral_callqueue_members(call_queue_id,cq_name,cq_extension):
	try:
		resp = connectRequest('/restapi/v1.0/account/~/call-queues/'+str(call_queue_id)+'/presence')
		call_queue_members = json.loads(resp.text())

		# Initialise default variable values to protect against loop crash if a call queue has no members.
		cq_member = str('No member')
		cq_member_ext = ''
		cq_member_accept_current_queue_calls = ''
		cq_member_accept_calls = ''

		for member in call_queue_members['records']:
			cq_member = member.get('member', {}).get('name')
			if cq_member:
				cq_member_ext = member.get('member', {}).get('extensionNumber')
				cq_member_accept_current_queue_calls = member.get('acceptCurrentQueueCalls')
				cq_member_accept_calls = member.get('acceptQueueCalls')
			else:
				cq_member = str('No member')
				cq_member_ext = ''
				cq_member_accept_current_queue_calls = ''
				cq_member_accept_calls = ''

			print(f'\u2192 Name: {cq_member} - Member Extension: {cq_member_ext} - Accept Current Queue Calls: {cq_member_accept_current_queue_calls} - Accept Queue Calls: {cq_member_accept_calls}')
			build_datalist(cq_name,cq_extension,cq_member,cq_member_ext,cq_member_accept_calls, cq_member_accept_current_queue_calls)
		
		# If no members found in any call queues, build list retrieving call queue details but populate 'No Members'
		if not call_queue_members['records']:
			
			build_datalist(cq_name,cq_extension,cq_member,cq_member_ext,cq_member_accept_calls, cq_member_accept_current_queue_calls)
	except Exception as e:
		sys.exit("error occured: " + str(e))

# Uses the collected call queue information to build a dictionary.
def build_datalist(cq_name,cq_extension,cq_member,cq_member_ext, cq_member_accept_calls, cq_member_accept_current_queue_calls):

	call_queue_datalist.append({
		"Call Queue Name":      				cq_name,
		"Call Queue Extension": 				cq_extension,
		"Call Queue Member":    				cq_member,
		"Member Extension":     				cq_member_ext,
		"Accept Queue Calls?":					cq_member_accept_calls,
		"Accept Current Queue Calls?":	cq_member_accept_current_queue_calls
	})
	build_csv(call_queue_datalist)

# Builds the csv file, sets headers. 
def build_csv(call_queue_datalist):
	folder_name = 'AuditResults'
	file_name = 'CallQueueAudit.csv'
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)
	file_path = os.path.join(folder_name, file_name)
	datalist_jsondump = json.dumps(call_queue_datalist)
	datalist_json = json.loads(datalist_jsondump)
	with open(file_path, "w", newline='', encoding="utf-8") as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=datalist_json[0].keys())
		writer.writeheader()
		for row in datalist_json:
			writer.writerow(row)

# Start Execution
if __name__ == "__main__":
		main_callqueue()
