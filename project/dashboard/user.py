import os

from flask import current_app
from flask_login import UserMixin
from google.cloud import bigquery

from project.globals import logger


class User(UserMixin):
    def __init__(self, id_, name, email):
        self.id = id_
        self.name = name
        self.email = email

    @staticmethod
    def get(user_id):
        # reset the creds
        # just use the User tables in the (unused) data dictionary project for now
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_project.json"
        # TODO: replace with insert/select on the main db

        SEARCH_USER = """
        #standardSQL
        SELECT * FROM data_dictionary.users WHERE id = '{id}'
        """
        query = SEARCH_USER.format(id=user_id)
        client = bigquery.Client()
        dataset_ref = client.dataset('data_dictionary')
        query_job = client.query(query)
        results = query_job.result()
        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        if not results:
            return None
        for row in results:
            user = User(
                id_=row[0], name=row[1], email=row[2]
            )
            logger.info(f"RETURNED USER: {user}")
            return user

    @staticmethod
    def create(id_, name, email):
        # reset the creds
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_app.creds_dir}/creds_project.json"

        client = bigquery.Client()
        dataset_ref = client.dataset('data_dictionary')
        table_ref = client.dataset('data_dictionary').table('users')
        table = client.get_table(table_ref)
        result = client.insert_rows(table, [(id_, name, email)])
        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        for row in result:
            logger.info(f"INSERTED USER: {row}")
