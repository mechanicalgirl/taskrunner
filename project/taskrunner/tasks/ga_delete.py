## python3 delete.py --chorusid {chorusid)
## API docs: https://developers.google.com/analytics/devguides/config/userdeletion/v3

from datetime import datetime
import os
import sys

from apiclient.discovery import build
from flask import current_app
from google.cloud import bigquery
from google.oauth2 import service_account

from project.globals import logger

property_ids = {
    '58639082': ('UA-189494-74', 'curbed'),
    '58640075': ('UA-189494-73', 'eater'),
    '58649526': ('UA-189494-75', 'racked'),
    '151990851': ('UA-29192711-1', 'polygon'),
    '56211076': ('UA-29192711-1', 'polygon'),
    '80041901': ('UA-46415601-1', 'recode'),
    '2435288': ('UA-1367699-1', 'sbnation'),
    '83037401': ('UA-48698701-1', 'vox'),
    '51978513': ('UA-26533115-1', 'theverge'),
    '119309609': ('UA-55396624-1', 'voxcreative'),
    '91986438': ('UA-55396624-1', 'voxcreative'),
    '79304634': ('UA-45903948-1', 'voxmedia')
}
#   '': ('UA-57276808-2', 'explainer'),
#   '': ('UA-57276808-3', 'voxrollup'),

class GADeletionTask(object):

    def __init__(self):
        pass

    def authenticate_service(self):
        """ Build the authenticated service object """
        SCOPES = ['https://www.googleapis.com/auth/analytics.user.deletion']
        ## These will be the creds associated with the user deletion service account in phrasal-alpha:
        SERVICE_ACCOUNT = f"{current_app.creds_dir}/creds_phrasal-alpha-839.json"
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT, scopes=SCOPES)
        try:
            service_object = build('analytics', 'v3', credentials=credentials, cache_discovery=False)
            logger.info(f"Valid service object: {service_object}")
            return service_object
        except Exception as e:
            logger.info(f"Invalid service object: {e}")
            sys.exit()
    
    def delete_user_by_clientid(self, analytics, clientid, propertyid):
        user_deletion_request_resource = analytics.userDeletion().userDeletionRequest()
        body = {
            'deletionRequestTime': str(datetime.now()),
            'kind': 'analytics#userDeletionRequest',
            'id': {'type': 'CLIENT_ID', 'userId': clientid},
            'webPropertyId': propertyid
        }
        logger.info(f"body: {body}")
        try:
            deletion_request = user_deletion_request_resource.upsert(body=body).execute()
            logger.info(f"deletion_request: {deletion_request}")
            logger.info(f"Deleted: {deletion_request['deletionRequestTime']}")
        except Exception as e:
            logger.info(f"Deletion error: {e}")
            return f"Deletion error: {e}"
 
        return "Success"
    
    def get_clientid_and_network(self, chorusid):
        client = bigquery.Client()
        GETIDS = """
        SELECT chorusid, clientid, network
        FROM `nymag-analytics-157315.dbt.dim__chorusid_visits`
        WHERE chorusid = '{chorusid}'
        """
        query_job = client.query(GETIDS.format(chorusid=chorusid))
        rows = query_job.result()
        r = []
        for row in rows:
            if row.clientid:
                r.append((row.clientid, row.network))
        row_list = list(set(r))

        total_bytes_billed = query_job.total_bytes_billed
        job_cost = round(total_bytes_billed * (500.0 / (1024*1024*1024*1024)), 2)

        return (row_list, job_cost)
    

    def run(self, **kwargs):
        message = None
        status = 500     # default; return 200 on success
        cost = 0         # default; return cost based on query_job if applicable

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/nymag-analytics-ga-client-ui-deletion.json"

        clientid = kwargs['user_request'].get('request_meta', None).get('identifiers', None).get('ga_clientid', None)
        if clientid:
            clientids = [(clientid, '79304634')]  # TODO: replace the second element with a network value, if we get one
        if not clientid:
            chorusid = kwargs['user_request'].get('chorus_user_id', None)
            if not chorusid:
                logger.info("You must provide a Chorus ID or nymcid")
                message = f"No Chorus ID in user request"
   
            # taskrunner will only ever be processing 1 client id at a time,
            # could rework the below method and code to return only 1 client id
            (clientids, cost) = self.get_clientid_and_network(chorusid)
            if not clientids:
              status = 200
              message = f"No client ids found to delete"

        for c in clientids:
            clientid = c[0]
            network = c[1]
            propertyid = property_ids[network][0]
            propertyname = property_ids[network][1]
    
            try:
                logger.info(f"Deleting clientId {clientid} for network {network} ({propertyid})")
                service_object = self.authenticate_service()
                self.delete_user_by_clientid(service_object, clientid, propertyid)
                message = f"clientId {clientid} deleted for network {network} ({propertyid})"
                status = 200
            except Exception as e:
                logger.info(f"Error: {e}")
                message = f"Error: {e}"

        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        return {'status': status, 'message': message, 'cost': cost}
