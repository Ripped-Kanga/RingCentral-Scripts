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
Clone the repo into a directory and open your terminal in the RingCentral-Scripts folder. You can also download the zipped release from Releases. Extract this to a choosen directory and open your terminal in RingCentral-Scripts-(version) folder. 

## Setup Python Virtual Environment (Optional) (Recommended)
### Linux & Mac
*Example*:

To create virtual environment - `python3 -m venv venv`.

To **activate**, run - `source venv/bin/acivate`.
### Windows
*Example*:

To create virtual environment - `python -m venv venv`.

To **activate**, run - `venv\Scripts\activate`.

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

After adding the App Client ID, App Secret, and JWT, rename the template file to .env (For Windows and Mac, make sure hidden files option is enabled in Explorer(Windows) and Finder(Mac))


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
- [x] Extension Direct Number
- [x] Email
- [x] Departments
- [x] Permissions (is administrator?)
- [x] User Assigned Role
- [x] Status
- [x] Setup Wizard State
- [x] Site
- [x] DND Status
- [x] Business Hours Forward Destination
- [x] After Hours Forward Destination
#### User Device Information
- [x] Device Name
- [x] Device Model
- [x] Device Serial
- [x] Device Status

### Features
- [x] Customisable API filtering.
- [x] Customisable fields export, allowing the user to pick what they want to export to csv (API is only polled for what is selected.)

## Call Queue Information
- [x] Call Queue Name
- [x] Call Queue Extension
- [x] Call Queue Members
- [x] Call Queue Member Queue Switch Status
- [x] Call Queue Memeber Global Switch Status

## Phone Numbers Information
- [x] Retrieve All Numbers
- [x] Phone Number Type
- [x] Phone Number Status
- [x] Filter Numbers based off filter parameters (Company Numbers, Direct Numbers, Inventory, Phone Line)


# Implementation Tracking (v0.97-alpha)

## General


## Audit.py
- [x] API filtering moved into a new subfunction for cleaner code and allow users to chain parameters together (?type=User&status=Disabled)
- [x] If a call queue is selected in the API filtering, either by direct choice or through broader filtering, always create a seperate more detailed CallQueue csv file that includes enhanced call queue presence details. 

## CallQueueAudit.py
- [x] Deprecated as of V0.97-alpha

## PhoneNumberAudit.py
- [x] Deprecated as of V0.97-alpha

# Implementation Tracking (v0.95-alpha)

## General
### Error Handling
- [x] Implemented first try at catching http codes in API exception stack.
	- [x] 404 Code Catch, treat as missing value and skip over.
	- [x] 400 Code does not return status_code, so extract API error from exception body and catch that way. Currently catching "HTTP Error 400, AWR-193 Answering Rule not supported"
	- [x] Any 500 Code, simply sleep the script and try again.
- [x] Interactive audit name at the beginning of script run. 

### Logging
- [x] Added first implementation of logging. Output is to .log file and console. Logging is enabled by setting DEBUG=1 in .env file. 

## UserAudit.py
- [x] Fixed VideoPro accounts crashing script due to no device record existing.
- [x] Added csv_field_type, csv_field_subType, csv_field_ahr to export options. 
- [x] Added After Hours Rule data
- [x] Added full API filtering control before csv field selection. Return full extension count and then post filter extension count. If no extensions are returned from the new filter parameters, ask user to try again. 
	- [ ] Move this into a new subfunction for cleaner code and allow users to chain parameters together (?type=User&status=Disabled)
- [x] Added Direct Number to auditable fields. 

## CallQueueAudit.py


## PhoneNumberAudit.py
