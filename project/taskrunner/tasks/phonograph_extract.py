import io
import json
import os
import sys
import time

from flask import current_app
from google.cloud import bigquery, storage

from project.globals import logger
from project.globals.database import Database
from project.taskrunner.utils import check_gcs_file, push_gcs_file


class PhonographExtractTask(object):

    def __init__(self):
        ENV = os.environ.get('ENV', 'staging')

        self.dataset = 'phonograph_events_prod'
        self.gcs_bucket = 'phonograph_extract_prod'
        """
        # use this when it's running in production
        self.dataset = 'phonograph_events_stage'
        self.gcs_bucket = 'phonograph_extract_stage'
        if ENV == 'production':
            self.dataset = 'phonograph_events_prod'
            self.gcs_bucket = 'phonograph_extract_prod'
        """

        """
        two gcs buckets, both have retention set for two days (files cannot be overwritten or deleted manually)
        phonograph_extract_prod
        phonograph_extract_stage
        """
        self.table = "pageload_stream"
        self.partition_limit = "2018-05-20 00:00:00"   # how do we determine how far back to go?
        # self.partition_limit = "2020-12-20 00:00:00"    ## TODO: make this a test value

    def extract_by_uuid(self, uuid):
        filename = f"{uuid}-extract.json"
        logger.info(f"EXTRACTING uuid FROM {self.dataset}.{self.table} INTO {self.gcs_bucket} {filename}")
        time.sleep(5)

        EXTRACT = """
          WITH t AS 
            (SELECT * FROM `voxmedia-phonograph.{dataset}.{table}`
              WHERE uid = '{uuid}' AND _PARTITIONTIME >= '{partlimit}')
          SELECT TO_JSON_STRING(t) AS json FROM t
        """
        query = EXTRACT.format(dataset=self.dataset, table=self.table, uuid=uuid, partlimit=self.partition_limit)
        client = bigquery.Client()
        dataset_ref = client.dataset(self.dataset)
        query_job = client.query(query)
        results = query_job.result()

        total_bytes_processed = query_job.total_bytes_processed
        total_bytes_billed = query_job.total_bytes_billed
        job_cost = round(total_bytes_billed * (500.0 / (1024*1024*1024*1024)), 2)
        # round(total_bytes_billed * (500.0 / (1024*1024*1024*1024)), 2)       # in cents
        # round(total_bytes_billed * (500.0 / (1024*1024*1024*1024))/100, 2)   # in dollars

        try:
            results_obj = [x.json for x in results][0]
            # logger.info(f"RESULTS OBJ {results_obj}")
            target_file = f"{uuid}-extract.json"
            gcs = push_gcs_file(self.gcs_bucket, results_obj, target_file)
        except Exception as e:
            logger.info(f"No phonograph records for this UUID. {str(e)}")
            target_file = f"empty-{uuid}-extract.json"
            push_gcs_file(self.gcs_bucket, '{}', target_file)
            return ("No phonograph records for this UUID.", 0)
        return (gcs, job_cost)

    def run(self, **kwargs):
        """
        This is the only required method in a task - everything else is flexible
        Always return a value for `message` to be included in the response
        Include a status of 200 (success) or 500 (failure)
        """
        message = None
        status = 500     # default; return 200 on success
        cost = 0         # default; return cost based on query_job if applicable

        # these are creds associated with a data-privacy-request-management service account
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_vox-data-lake.json"

        uuid = kwargs['user_request'].get('request_meta', None).get('identifiers', None).get('uuid', None)
        if uuid:
            extract_name = f"{uuid}-extract.json"
            extract = check_gcs_file(self.gcs_bucket, extract_name)
            if extract:
                message = extract
                status = 200
            else:
                try:
                    (message, cost) = self.extract_by_uuid(uuid)
                    status = 200
                except Exception as e:
                    message = str(e)
        else:
            message = "UUID not found in user request or lookup"
            status = 200

        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        return {'status': status, 'message': message, 'cost': cost}
