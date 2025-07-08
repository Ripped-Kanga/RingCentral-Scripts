#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to conduct audits on users. 
Version:  0.1
Github:   https://github.com/Ripped-Kanga/RingCentral-Scripts
"""
# Import libraries
import os
import sys
import json
import time
import datetime
from RingCentralMain import connection_test, connectRequest, audit_checker

# Global Variables
start_time = datetime.datetime.now()

# Start main thread
def main_user():
	print (f'Script Start Time: {start_time}')
	connection_attempt = connection_test()
	if connection_attempt:
		print ("Proceeding with User Audit, note that as a minimum, the 'User' type is already filtered for.")
		user_count, built_url = audit_checker('/restapi/v1.0/account/~/extension?type=User')
		get_ringcentral_users(built_url)
	else:
		sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")


def get_ringcentral_users(built_url):
	resp = connectRequest(built_url)
	user_count = []
	for record in resp.json().records:
		print (f'{record.name} - {record.extensionNumber}')
		user_count.append(record.id)
	print (len(user_count))




# Start Execution
if __name__ == "__main__":
	main_user()
