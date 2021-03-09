import os
import sys
import time

from flask import current_app
from google.cloud import bigquery

from project.globals import logger
from project.taskrunner.utils import check_gcs_file


class PhonographDeleteTask(object):
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
        self.partition_limit = "2018-05-20 00:00:00"

    def remove_by_uuid(self, uuid):
        logger.info(f"Preparing to REMOVE ROWS FROM {self.dataset}.{self.table} FOR {uuid}")
        time.sleep(5)

        ## TODO: are some of these methods generic enough that they could be moved out to a BigQuery utility class?

        partitions = None
        tmp_table= None
        delete_from_temp = None

        cost = 0

        (last_partition, cost_stepone) = self.identify_last_partition()
        cost += cost_stepone

        if last_partition:
            (partitions, cost_steptwo) = self.identify_partition_uuid(last_partition, uuid)
            cost += cost_steptwo

        if partitions:
            logger.info(f"{len(partitions)} partitions found.")
            (tmp_table, cost_stepthree) = self.copy_partition(partitions)
            cost += cost_stepthree
        else:
            logger.info("No partitions with given UUID found, exiting.")
            ## TODO: what do we do with the cost if we exit at this point?
            return False

        if tmp_table:
            (delete_from_temp, cost_stepfour) = self.delete_on_temp(tmp_table, uuid)
            logger.info(f"delete_from_temp {delete_from_temp}")
            cost += cost_stepfour

        if delete_from_temp:
            (copyback, cost_stepfive) = self.copy_back_partitions(tmp_table, partitions)
            cost += cost_stepfive

        logger.info(f"Phonograph deletion completed at cost of {cost} cents")
        logger.info(f"Optional: 'bq rm {self.dataset}.{tmp_table}' after QAing the result.")

        return (True, cost)

    def run_query(self, query):
        client = bigquery.Client()
        query_job = client.query(query)

        result = query_job.result()
        result_obj = [x for x in result]

        duration = self.get_duration(query_job)
        cost = self.get_cost(query_job)

        return (result_obj, cost)

    def identify_last_partition(self):
        """Identify the last partition that is being streamed into, do not attempt to alter it"""
        logger.info("Identify the last partition that is being streamed into, do not attempt to alter it")
        QUERY = """
          SELECT DATE(MAX(_PARTITIONTIME)) as pt FROM `voxmedia-phonograph.{dataset}.{table}`
        """
        query = QUERY.format(dataset=self.dataset, table=self.table)
        (result, cost) = self.run_query(query)
        try:
            result_obj = result[0].pt
        except Exception as e:
            logger.info(f"Error retrieving last partition {str(e)}")
            return False
        return (result_obj, cost)

    def identify_partition_uuid(self, last_partition, uuid):
        """Identify which partitions this UUID is present in"""
        logger.info("Identify which partitions this UUID is present in")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_vox-data-lake.json"

        QUERY = """
          SELECT DATE(_PARTITIONTIME) as pt
          FROM `vox-data-lake.maestro_prod.phonograph_pageload_uids`
          WHERE _PARTITIONTIME <> "{last_partition} 00:00:00"
            AND _PARTITIONTIME > '{partition_limit}'
            AND uid = '{uuid}'
            GROUP BY 1 ORDER BY 1
        """
        query = QUERY.format(last_partition=last_partition, partition_limit=self.partition_limit, uuid=uuid)
        (result, cost) = self.run_query(query)
        result_obj = [x.pt for x in result]

        # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_voxmedia-phonograph.json"
        # these are creds associated with a data-privacy-request-management service account
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_vox-data-lake.json"

        return (result_obj, cost)

    def copy_partition(self, partitions):
        """Copy each partition to a TMP table"""
        logger.info("Copy each partition to a TMP table")

        tmp_table = f"tmp_gdpr_{self.table}"
        client = bigquery.Client()

        logger.info(f"Removing (if exists) {self.dataset}.{tmp_table}")
        table_id = f"voxmedia-phonograph.{self.dataset}.{tmp_table}"
        client.delete_table(table_id, not_found_ok=True)
        logger.info(f"Deleted table '{table_id}'")

        """
        # https://cloud.google.com/bigquery/docs/creating-partitioned-tables#creating_an_ingestion-time_partitioned_table_when_loading_data
        # You can create an ingestion-time partitioned table by specifying partitioning options when you load data into a new table.
        # You do not need to create an empty partitioned table before loading data into it.
        # You can create the partitioned table and load your data at the same time.
        logger.info(f"Making a new partitioned temp table at {self.dataset}.{tmp_table}")
        cmd = f"bq mk --time_partitioning_type=DAY {self.dataset}.{tmp_table}"
        logger.info(f"{cmd}")
        os.system(cmd)
        """

        logger.info(f"Copying the partitions to {self.dataset}.{tmp_table}")
        cost = 0
        for p in partitions:
            part = str(p).replace('-', '')
            source_table_id = f"voxmedia-phonograph.{self.dataset}.{self.table}${part}"
            destination_table_id = f"voxmedia-phonograph.{self.dataset}.{tmp_table}${part}"
            try:
                query_job = client.copy_table(source_table_id, destination_table_id)
                query_job.result() # blocking, waits for job to complete
                duration = self.get_duration(query_job)
                cost += self.get_cost(query_job)
            except Exception as e:
                logger.info(f"Error copying partitions: {str(e)}")
                return False

        logger.info(f"Total cost for all partitions: {cost}")
        logger.info(f"Copy DONE.")

        return (tmp_table, cost)

    def delete_on_temp(self, tmp_table, uuid):
        """Run delete on the TMP tables"""
        logger.info(f"Running delete on {self.dataset}.{tmp_table}")
        QUERY = """
          DELETE FROM `voxmedia-phonograph.{dataset}.{table}` WHERE uid = '{uuid}'
        """
        query = QUERY.format(dataset=self.dataset, table=tmp_table, uuid=uuid)
        (result, cost) = self.run_query(query)
        return (result, cost)

    def copy_back_partitions(self, tmp_table, partitions):
        """Copy the partitions back into $DATASET.$TABLE"""
        logger.info(f"Copy the partitions back into {self.dataset}.{self.table}")

        client = bigquery.Client()

        cost = 0
        for p in partitions:
            part = str(p).replace('-', '')
            source_table_id = f"voxmedia-phonograph.{self.dataset}.{tmp_table}${part}"
            destination_table_id = f"voxmedia-phonograph.{self.dataset}.{self.table}${part}"
            try:
                job_config = bigquery.CopyJobConfig()
                # copy over existing partitions
                job_config.write_disposition = "WRITE_TRUNCATE"
                query_job = client.copy_table(
                    source_table_id,
                    destination_table_id,
                    job_config=job_config)
                query_job.result() # blocking, waits for job to complete
                duration = self.get_duration(query_job)
                cost += self.get_cost(query_job)
            except Exception as e:
                logger.info(f"Error copying back partitions: {str(e)}")
                return False

        logger.info(f"Total cost for all partitions: {cost}")
        logger.info(f"Copy DONE.")

        return (True, cost)

    def get_duration(self, job):
        duration = (job.ended - job.started).total_seconds()
        logger.info(f"Completed {job.job_id} in {duration} seconds")
        return duration

    def get_cost(self, job):
        cost = 0
        try:
            total_bytes_billed = job.total_bytes_billed
            cost = round(total_bytes_billed * (500.0 / (1024*1024*1024*1024)), 2)
            logger.info(f"Cost for {job.job_id} is {cost} cents")
        except Exception as e:
            logger.info(f"Cost cannot be calculated for this job type")
        return cost

    def run(self, **kwargs):
        """
        This is the only required method in a task - everything else is flexible
        Always return a value for `message` to be included in the response
        Include a status of 200 (success) or 500 (failure)
        """
        message = None
        status = 500     # default; return 200 on success
        cost = 0         # default; return cost based on query_job if applicable


        # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_voxmedia-phonograph.json"
        # these are creds associated with a data-privacy-request-management service account
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_vox-data-lake.json"

        ## TODO: add better error handling

        uuid = kwargs['user_request'].get('request_meta', None).get('identifiers', None).get('uuid', None)
        # TODO: uuid is getting populated with 'n/a' in the spreadsheet when it should be empty -
        # handle that error here or in the API?
        if uuid:
            (deletion, cost) = self.remove_by_uuid(uuid)
            if deletion:
                message = f"Deletion completed: {deletion}"
                status = 200
        else:
            logger.info(f"No UUID in user request")
            message = f"No UUID in user request"
            status = 200

        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        return {'status': status, 'message': message, 'cost': cost}
