# python3 import.py

# standalone script - the API endpoint needs to be available to run this

# where the data comes from:
# The privacy spreadsheet:
#   https://docs.google.com/spreadsheets/d/16w6p8kOvmXwsg47506EwqfHCdAhW596Kuq1YwG2VnGM/edit#gid=1003431616
# is connected to this view:
#   https://console.cloud.google.com/bigquery?p=voxmedia-data-dictionary&d=privacy_requests&t=privacy_requests
# then a scheduled query runs against the view:
#   https://console.cloud.google.com/bigquery/scheduled-queries/locations/us/configs/60b7494a-0000-2fb1-88c6-240588707560/runs?project=voxmedia-data-dictionary
# and populates this table, which is what we query in this script:
#   https://console.cloud.google.com/bigquery?p=voxmedia-data-dictionary&d=privacy_requests&t=privacy_requests_transfer

from datetime import date, datetime
import json
import os
import requests
import sys

from google.cloud import bigquery
import xlrd

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./creds/creds_voxmedia-data-privacy.json"

# 1. get the rows from bigquery
SEL = """
  SELECT request_number, timestamp, email, ticket, request_type,
      name, user_id, ga_clientid, vm_suid, vm_uuid, permutive_id, details
  FROM `voxmedia-data-dictionary.privacy_requests.privacy_requests_transfer`
  WHERE complete = "FALSE"
"""
client = bigquery.Client()
query_job = client.query(SEL)
results = query_job.result()

# 2. convert each row to a json packet
for row in results:
    print(f"New record: {row}")
    details = None
    if row.details:
        details = row.details.replace('"', '').replace('!', '')

    # date format changed in the latest spreadsheet update,
    # but keep this around jic
    #
    # xltimestamp = float(row.timestamp)
    # rd = xlrd.xldate.xldate_as_tuple(xltimestamp, 0)
    # date_obj = date(year=rd[0], month=rd[1], day=rd[2])

    date_obj = datetime.strptime(row.timestamp, '%m/%d/%Y')
    request_date = date_obj.strftime("%Y-%m-%d")

    uuid = row.vm_uuid
    if uuid == 'n/a':
        uuid = ''
    suid = row.vm_suid
    if suid == 'n/a':
        suid = ''
    permutive_id = row.permutive_id
    if permutive_id == 'n/a':
        permutive_id = ''

    obj = {
        "request_type": row.request_type,
        "email": row.email,
        "request_date": request_date,
        "chorus_user_id": row.user_id,
        "request_meta": {
            "name": row.name,
	    "request_id": row.request_number,
	    "ticket_id": row.ticket,
	    "details": details,
	    "identifiers": {
	        "uuid": row.vm_uuid,
	        "suid": row.vm_suid,
	        "permutive_id": row.permutive_id,
	        "ga_clientid": row.ga_clientid
	    }
        }
    }
    json_obj = json.dumps(obj)

    # 3. post each one to the API, log the response
    # command = f"curl -X POST http://localhost:5001/userrequest/ -H 'Content-Type: application/json' -d '{json_obj}'"
    url = 'http://localhost:5001/userrequest/'
    files = {'file': ('userrequest.json', json_obj)}
    r = requests.post(url, files=files)
    print(f'Response: {r.text}')

del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
