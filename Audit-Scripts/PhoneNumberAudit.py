#!/usr/bin/python
"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to collect information on the registered phone numbers to the RingCentral Account.
Version:  0.1
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
'''
This script will be used to retrieve -> Company Numbers, Direct Numbers, Temporary Numbers
'''