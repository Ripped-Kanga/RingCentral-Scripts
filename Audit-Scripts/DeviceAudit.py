#!/usr/bin/python

"""
Author:   Alan Saunders
Purpose:  Uses the RingCentral API to conduct audits on devices and export the results to csv.
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

# Global Variables
start_time = datetime.datetime.now()
