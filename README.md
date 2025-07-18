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
## CallQueueAudit.py
- [x] Implement rate limit checking and prevention.
- [x] Implement audit scope limit, display how many queues exist on the RingCentral instance and ask the user how many they want to audit. 
- [ ] Audit based off call queue name, useful if you only need info on one call queue. Should accept Call Queue Name or Call Queue Extension
- [ ] Optional: After running audit, ability to find all call queues one member is apart of, only print to console???

## UserAudit.py
- [x] Build initial version, test and debug.
- [x] Write audit data to csv
- [ ] Should pull the following:
	### User Information
	- [x] First & Last Name
	- [x] Extension Number
	- [x] Email
	- [x] Contact Number
	- [x] Company Name
	- [x] Departments
	- [x] Permissions (is administrator?)
	- [x] Status
	- [x] Setup Wizard State
	- [x] Site
	- [ ] Service Features (Voicemail, SMS, DND, Presence, International Dial Out, Call Forwarding, ect...)
	### User Device Information
	- [ ] Device Name
	- [ ] Device URI
	- [ ] Device Caller ID
