import os

from flask import current_app
from google.cloud import bigquery

from project.globals import logger
from project.globals.database import Database
from project.taskrunner.utils import check_gcs_file, push_gcs_file


class EntriesNullTask(object):

    def __init__(self):
        ENV = os.environ.get('ENV', 'staging')

        self.dataset = 'chorus_db_prod'
        """
        self.dataset = 'chorus_db_stage'
        if ENV == 'production':
            self.dataset = 'chorus_db_prod'
        """
        self.table = "entries"

    def update_chorus_entry(self, chorus_id):
        UPDATE = """
        UPDATE `vox-data-lake.chorus_db_prod.entries`
        SET user_id = NULL WHERE user_id = {chorus_id};
        """
        query = UPDATE.format(chorus_id=chorus_id)
        client = bigquery.Client()
        query_job = client.query(query)

        results = query_job.result()
        updated_rows = query_job.num_dml_affected_rows

        total_bytes_billed = query_job.total_bytes_billed
        job_cost = round(total_bytes_billed * (500.0 / (1024*1024*1024*1024)), 2)

        return (updated_rows, job_cost)

    def run(self, **kwargs):
        """
        This is the only required method in a task - everything else is flexible
        Always return a value for `message` to be included in the response
        Include a status of 200 (success) or 500 (failure)
        """
        message = None
        status = 500     # default; return 200 on success
        cost = 0         # default; return cost based on query_job if applicable

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_vox-data-lake.json"

        chorus_id = kwargs['user_request'].get('chorus_user_id', None)
        if chorus_id:
            try:
                (update, cost) = self.update_chorus_entry(chorus_id)
                status = 200
                if update:
                    message = f"Chorus user id nullified in `vox-data-lake.chorus_db_prod.entries`"
                else:
                    message = 'Chorus id not found in `vox-data-lake.chorus_db_prod.entries`'
            except Exception as e:
                logger.info(f"Chorus entry update error: {e}")
        else:
            status = 200
            message = f"No Chorus user id in user request"

        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        return {'status': status, 'message': message, 'cost': cost}
