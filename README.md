# RingCentral-Scripts
A collection of scripts that interact with the RingCentral API. This project is worked on in my spare time, and is regularly updated currently. Features are added regularly. Currently, the project can:
- Audit User Accounts 
- Audit Call Queues
- Audit Phone Numbers

All audit results are exported to csv file stored in AuditResults folder.

## Future Project Goals:
- Further improve existing logic flows and unify execution experience (execute one script, pick what you want to audit)
- Explore feasibility of producing basic call flow diagrams for Users / Company flow.
- Add additional audits where applicable (Audit Trail, Call Log, ect...)

# Dependancies 
## Python3 
Download the latest Python3 binary and install it.

# Download & Execution
Clone the repo into a directory and open your terminal in the RingCentral-Scripts folder.

## Setup Python Virtual Environment (Optional)
### Linux & Mac
`python3 -m venv /path/to/new/virtual/environment`.
To activate, run `source /path/to/new/virtual/environment/bin/activate`
### Windows
`python -m venv /path/to/new/virtual/environment`
to activate, run `venv\Scripts\activate`

### Required Libraries
From terminal, run: (If you are going to use a Python Virtual Environment, do this after activating the environment)
	- `pip install ringcentral`
	- `pip install dotenv`
	- `pip install pick`

# Populate .env
You get the environment parameters from your
application dashbord in your developer account
https://developers.ringcentral.com/my-account.html#/applications

You will need to register an app and choose JWT Auth Flow as your Auth method. Your app will need `Read Accounts` & `Read Presence` permissions.
Copy your APP Client ID, App Client Secret, and JWT Credential Secret into your .env file.
https://developers.ringcentral.com/console/my-credentials

Refer to the .env_template for an example.


# Execution
Run the script you wish to run, below example has used `UserAudit.py`
## Linux & Mac
`python3 Audit-Scripts/UserAudit.py`

## Windows
`python Audit-Scripts\UserAudit.py`

# Supported Audits:
## User Information
- [x] First & Last Name
- [x] Extension Number
- [x] Email
- [x] Departments
- [x] Permissions (is administrator?)
- [x] User Assigned Role
- [x] Status
- [x] Setup Wizard State
- [x] Site
- [x] DND Status
- [x] Business Hours Forward Destination
	### User Device Information
	- [x] Device Name
	- [x] Device Model
	- [x] Device Serial
	- [x] Device Status
- [x] Customisable fields export, allowing the user to pick what they want to export to csv (API is only polled for what is selected.)

## Call Queue Information
- [x] Call Queue Name
- [x] Call Queue Extension
- [x] Call Queue Members
- [x] Call Queue Member Queue Switch Status
- [x] Call Queue Memeber Global Switch Status
- [x] Limit the audit to x call queues (this is legacy from debugging and will be replaced with better fitlering parameters)

## Phone Numbers Information
- [x] Retrieve All Numbers
- [x] Phone Number Type
- [x] Phone Number Status
- [x] Filter Numbers based off filter parameters (Company Numbers, Direct Numbers, Inventory, Phone Line)

# Implementation Tracking
## General
- [x] Implement rate limit checking and prevention.
- [X] Improve API error handling.
- [x] Added filter options for initial API call to:
	- [x] UserAudit.py
	- [ ] CallQueueAudit.py
	- [x] PhoneNumberAudit.py

## UserAudit.py
- [x] Build initial version, test and debug.
- [x] Write audit data to csv
- [x] Selectable fields for CSV file export, does not consume API calls for unelected fields.
- [X] Add catch for running unfiltered params, skip unassigned extensions so as to not crash the script. 

- [x] Audits the following:
	### User Information
	- [x] First & Last Name
	- [x] Extension Number
	- [x] Email
	- [x] Departments
	- [x] Permissions (is administrator?)
	- [x] User Assigned Role
	- [x] Status
	- [x] Setup Wizard State
	- [x] Site
	- [x] DND Status
	- [x] Business Hours Forward Destination
	### User Device Information
	- [x] Device Name
	- [x] Device Model
	- [x] Device Serial
	- [x] Device Status

## CallQueueAudit.py
- [x] Redo script logic to better acommodate API limits and better error checking.
	- [x] Massively improved call queue audit performance, utilises different API call to retrieve call queue users.
	- [x] Improve error checking
		- [x] Will catch if a call queue has no members and write empty values to the csv for the member info. Call queue info will still be added.
- [x] Implement audit scope limit, display how many queues exist on the RingCentral instance and ask the user how many they want to audit. #will remove and replace with filter options similar to UserAudit.py
- [ ] Audit based off call queue name, useful if you only need info on one call queue. Should accept Call Queue Name or Call Queue Extension
- [ ] After running audit, ability to find all call queues one member is apart of, only print to console???

## PhoneNumberAudit.py
- [x] Build initial version, test and debug.
- [x] Write audit data to csv
- [x] Implement basic filter parameters. 
- [ ] Implement more advanced filter parameters

