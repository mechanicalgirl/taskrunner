import io
import os

from google.cloud import storage

from project.globals import logger

def push_gcs_file(gcs_bucket, obj, file_name):
    """Convert an object to a file and load to a given GCS bucket"""
    logger.info(f"Push GCS file: {gcs_bucket}/{file_name}")
    try:
        with io.open(file_name, 'w') as f:
            f.write(obj)
        client = storage.Client()
        bucket = client.get_bucket(gcs_bucket)
        blob = bucket.blob(file_name)
        with open(file_name, 'rb') as f:
            blob.upload_from_file(f)
        os.remove(file_name)
    except Exception as e:
        logger.info(f"Error loading file to GCS: {str(e)}")
        if str(e).startswith('403 PUT'):
            logger.info(f"The file has already been loaded to {gcs_bucket}")
            return f"{gcs_bucket}/{file_name}"
        return str(e)
    logger.info(f"Success loading file to GCS: {file_name}")
    return blob.public_url

def check_gcs_file(gcs_bucket, file_name):
    """Check that a file exists in the named GCS bucket"""
    logger.info(f"Look for GCS file: {gcs_bucket}/{file_name}")
    storage_client = storage.Client()
    bucket = storage_client.bucket(gcs_bucket)
    blob = bucket.get_blob(file_name)
    if blob:
        return blob.public_url
    return False
