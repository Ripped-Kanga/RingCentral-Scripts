#!/usr/bin/python
__version__ = "0.2"

# Import libraries
import os
import sys
import json
import time
import datetime
import csv
from RingCentralMain import housekeeping, connection_test, connectRequest, audit_checker
import pprint

# Global Variables
phone_audit_count = 0
datalist = []
start_time = datetime.datetime.now()


# Start main thread
def main_phone_number_audit():
	housekeeping()
	print (f'Script Start Time: {start_time}')
	connection_attempt = connection_test()
	if connection_attempt:
		print ("Proceeding with Phone Number audit.")
		filtered_phone_number_count, phone_number_count, built_url = audit_checker('/restapi/v2/accounts/~/phone-numbers')
		get_phone_numbers (filtered_phone_number_count, phone_number_count, built_url)
	else:
		sys.exit("API did not respond with 200 OK, please check your .env variables and credentails.")

	end_time = datetime.datetime.now()
	runtime = (end_time - start_time).total_seconds()
	m, s  = divmod(runtime, 60)

	print ("Script has completed, audit results:")
	if filtered_phone_number_count:
		print(f'Audited {phone_audit_count} phone numbers of {filtered_phone_number_count} found filtered phone numbers.')
	else:
		print (f'Audited {phone_audit_count} phone numbers of {phone_number_count} found phone numbers.')
	print (f'\nScript End Time:    {end_time}')
	print ("Script runtime was: {} minutes and {} seconds".format(int(m), int(s)))
	exit (0)

def get_phone_numbers(filtered_phone_number_count, phone_number_count, built_url):
	phone_number_resp = connectRequest(built_url)
	phone_number_data = json.loads(phone_number_resp.text())
	for phone_records in phone_number_data['records']:
		phone_number = phone_records.get('phoneNumber')
		phone_number_status = phone_records.get('status')
		phone_number_type = phone_records.get('usageType')
		row = {
					"Phone Number":					phone_number,
					"Phone Number Status":	phone_number_status,
					"Phone Number Type":		phone_number_type
				}
		datalist.append(row)

# Global variable so that user_main() can report the total audited users.
		global phone_audit_count
		phone_audit_count += 1
		if filtered_phone_number_count:
			print (f'\nAudited {phone_audit_count} of {filtered_phone_number_count} filtered numbers.\n')
			pprint.pprint(row, indent=2, sort_dicts=False)
		else:
			print (f'\nAudited {phone_audit_count} of {phone_number_count} numbers.\n')
			pprint.pprint(row, indent=2, sort_dicts=False)
	build_phone_numbers_csv(datalist)

#Builds the csv file, sets headers.
def build_phone_numbers_csv(datalist):
	folder_name = 'AuditResults'
	file_name = 'PhoneNumberAudit.csv'
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)
	file_path = os.path.join(folder_name, file_name)

	if not datalist:
		print ("No data in dictionary to write")
		return

	fieldnames = list(datalist[0].keys())
	with open(file_path, "w", newline='', encoding="utf-8") as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
		writer.writeheader()
		for row in datalist:
			writer.writerow(row)


# Start Execution
if __name__ == "__main__":
	#start main_phone_number_audit() and listen for keyboard interrupts
	try:
		main_phone_number_audit()
	except KeyboardInterrupt:
		print('\nInterrupted by keyboard CTRL + C, exiting...\n')
		try:
			sys.exit(130)
		except SystemExit:
			os._exit(130)
