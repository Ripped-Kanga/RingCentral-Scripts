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
from RingCentralMain import connection_test, connectRequest, audit_checker

# Global Variables
start_time = datetime.datetime.now()

# Start main thread
def main_user():
	print (f'Script Start Time: {start_time}')
	connection_attempt = connection_test()
	if connection_attempt:
		user_count, built_url = audit_checker('/restapi/v1.0/account/~/extension')
		get_ringcentral_users(built_url)
	else:
		sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")


def get_ringcentral_users(built_url):
	resp = connectRequest(built_url)
	user_count = []
	for record in resp.json().records:
		print (record.name)
		user_count.append(record.id)
	print (len(user_count))




# Start Execution
if __name__ == "__main__":
	main_user()
