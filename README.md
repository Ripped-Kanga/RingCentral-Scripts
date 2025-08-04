# RingCentral-Scripts
A collection of scripts that interact with the RingCentral API

# Dependancies 
## Python3 
- Required Libraries
	- `pip install ringcentral` # RingCentral SDK
	- `pip install dotenv` # .env support
	- `pip install pick` # console menu

# Populate .env
You get the environment parameters from your
application dashbord in your developer account
https://developers.ringcentral.com
Refer to the .env_template for an example.

# Setup Python Virtual Environment
## Linux & Mac
`python3 -m venv /path/to/new/virtual/environment`.
To activate, run `source /path/to/new/virtual/environment/bin/activate`
## Windows
`python -m venv /path/to/new/virtual/environment`
to activate, run `venv\Scripts\activate`

# Execute
Invoke the script you wish to run, below example has used `CallQueueAudit.py`
## Linux & Mac
`python3 CallQueueAudit.py`

## Windows
`python CallQueueAudit.py`

# Implementation Tracking
## General
- [x] Implement rate limit checking and prevention.
- [ ] Improve API error handling.
- [x] Added filter options for initial API call to:
	- [x] UserAudit.py
	- [ ] CallQueueAudit.py

## CallQueueAudit.py
- [x] Redo script logic to better acommodate API limits and better error checking.
	- [x] Massively improved call queue audit performance, utilises different API call to retrieve call queue users.
	- [x] Improve error checking
		- [x] Will catch if a call queue has no members and write empty values to the csv for the member info. Call queue info will still be added.
- [x] Implement audit scope limit, display how many queues exist on the RingCentral instance and ask the user how many they want to audit.#will remove and replace with filter options similar to UserAudit.py
- [ ] Audit based off call queue name, useful if you only need info on one call queue. Should accept Call Queue Name or Call Queue Extension
- [ ] After running audit, ability to find all call queues one member is apart of, only print to console???

## UserAudit.py
- [x] Build initial version, test and debug.
- [x] Write audit data to csv
- [ ] Should pull the following:
- [ ] Store User IDs in json for later use, write IDs to csv file column one.
	### User Information
	- [x] First & Last Name
	- [x] Extension Number
	- [x] Email
	- [ ] Contact Number
	- [x] Departments
	- [x] Permissions (is administrator?)
	- [x] User Assigned Role
	- [x] Status
	- [x] Setup Wizard State
	- [x] Site
	- [x] DND Status
	### User Device Information
	- [x] Device Name
	- [x] Device Model
	- [x] Device Serial
	- [x] Device Status