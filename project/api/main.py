from datetime import datetime, timedelta
import json
import os
import sys

from flask import Blueprint, jsonify, request, current_app
from google.cloud import bigquery

from project.globals.database import Database
from project.globals.utils import get_statsd_client
from project.globals import logger


api_blueprint = Blueprint("api", __name__,)

@api_blueprint.route("/", methods=["GET"])
def home():
    print(f"{sys._getframe(0).f_code.co_name}")
    return 'Hello from the API service!'


## TODO: stub out a confirmation loop for future use

@api_blueprint.route("/userrequest/", methods=["POST"])
def user_request():
    """
    endpoint - accept the user request as a JSON object

    1) store the request and return a request id
    2) determine which tasks to run based on the request content (for now it's just the data eng tasks)
       Note: we could do the uid lookup based on chorus id here instead of relegating that to the tasks
    3) use task and user request ids to generate task instances in the postgres db

    curl -X POST http://localhost:5004/userrequest/ -H "Content-Type: application/json" -d '{"username":"abc","request_meta":"def"}'
    curl -X POST http://localhost:5004/userrequest/ -H "Content-Type: application/json" -d @user_request.json

    example JSON:
    https://gist.github.com/mechanicalgirl/6d60d4a6bc2ea9de1f3f6a637fecd362

    Note: This code makes a lot of assumptions about what the content of a request
      would look like, based on existing requests and the structure of the SBN
      contact form. It will definitely change - and impact the structure of the
      user request table - once this app is integrated with real requests,
      so I'm making my best guess for now.
    """

    content = request.get_json()
    if not content:
        if 'file' not in request.files:
            return "Missing file upload"
        bytefile = request.files['file'].read()
        cfile = bytefile.decode('utf-8')
        content = json.loads(cfile)

    new_request = validate_request(content)
    if not new_request:
        return "Invalid user request"

    # store the request and return a request id
    user_request_id = add_user_request(new_request)
    if not user_request_id:
        return "User request could not be stored"
    user_request = get_user_request(user_request_id)
    if not user_request:
        return "User request could not be returned"

    task_instances = []
    tasks = identify_tasks(user_request)
    if tasks:
        for task in tasks:
            task_instance = create_task_instance(task, user_request)
            task_instances.append(task_instance)

    if (len(task_instances) != len(tasks)) or (len(task_instances) == 0):
        user_request['notes'] = "Task instances could not be created. Check user request - is it missing a Chorus user id?"
        update_user_request(user_request)
        response_object = {
            "message": f"Task instances could not be created for user request {user_request['id']}"
        }
        return response_object, 200

    task_names = [x['name'] for x in tasks]
    response_object = {
        "message": f"Task instances {task_names}: {[x['id'] for x in task_instances]} created for user request {user_request['id']}"
    }
    return response_object, 200

def validate_request(user_request):
    if not isinstance(user_request, dict):
        logger.info(f"Incoming user request must be a dict")
        return False

    required = ('email', 'request_type', 'request_date')
    if not set(required).issubset(user_request):
        logger.info(f"Incoming user request must contain 'email', 'request_type', and 'request_date'")
        return False

    created_at = datetime.now()
    user_request['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S')

    # chorus_user_id must be an integer
    try:
        user_request['chorus_user_id'] = int(user_request['chorus_user_id'])
    except Exception as e:
        user_request['chorus_user_id'] = None

    if 'request_due_date' in user_request:
        deadline_date = datetime.strptime(user_request['request_due_date'], '%Y-%m-%d')
    else:
        deadline_date = created_at + timedelta(days=30)
    user_request['deadline_date'] = deadline_date.strftime('%Y-%m-%d %H:%M:%S')

    logger.info(f"Incoming user request validated")

    return user_request

def add_user_request(request_json):
    """Returns the user request id"""
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    statsd_client = get_statsd_client(current_app.config.get('STATSD_HOST', None))
    try:
        user_id = pg.create_user_request(request_json)
        logger.info(f"User request created '{user_id}'")
        if statsd_client:
            statsd_client.incr(f"api.user_request.success")
        return user_id
    except Exception as e:
        logger.info(f"User request could not be created: {str(e)}")
        if statsd_client:
            statsd_client.incr(f"api.user_request.fail")
        return None

def get_user_request(user_request_id):
    """Returns the user request object"""
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    try:
        user_request_obj = pg.get_user_request_by_id(user_request_id)
        logger.info(f"Request {user_request_id} returned")
        return user_request_obj
    except Exception as e:
        logger.info(f"Request {user_request_id} could not be returned: {str(e)}")
        return None

def identify_tasks(request):
    """ Return a list of tasks that can be run for this user """
    task_names = []
    tasks = []

    chorus_user_id = request.get('chorus_user_id', None)
    gaclientid = request.get('request_meta', None).get('identifiers', None).get('ga_clientid', None)
    uuid = request.get('request_meta', None).get('identifiers', None).get('uuid', None)
    if not uuid:
        uuid = get_uuid_by_chorus_id(chorus_user_id)
    if uuid:
        request['request_meta']['identifiers']['uuid'] = uuid
        update_user_request(request)

    r_type = request['request_type'].lower()
    request_type = ''
    if 'delet' in r_type:
        request_type = 'Delete'
    if any(x in r_type for x in ['extract', 'request']):
        request_type = 'Data Extract'

    if request_type == 'Delete':
        task_names = get_task_names('delete')
        if not chorus_user_id:
            logger.info("Chorus User ID not found in request")
            task_names.remove('Chorus Entries User Deletion')
            task_names.remove('Twitter Owner Nullify')
            if not gaclientid:
                logger.info("GA Client ID not found in request")
                task_names.remove('GA UI Deletion')
            if not uuid:
                logger.info(f"UUID not found in request")
                task_names.remove('Phonograph Delete')

    if request_type == 'Data Extract':
        task_names = get_task_names('extract')
        if not chorus_user_id:
            if not uuid:
                task_names.remove('Phonograph Extract')

    logger.info(f"Task names: {task_names}")

    for t in task_names:
        task = get_task(t)
        tasks.append(task)

    return tasks

def get_uuid_by_chorus_id(chorus_id):
    logger.info(f"Pulling uuid by Chorus id")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./project/api/creds/creds_vox-data-lake.json"
    CID_SELECT = """
      SELECT DISTINCT uid
      FROM `vox-data-lake.maestro_prod.phonograph_uid_gaid_chorusid_daily`
      WHERE chorus_id = "{chorus_id}"
    """
    query = CID_SELECT.format(chorus_id=chorus_id)
    client = bigquery.Client()
    query_job = client.query(query)
    results = query_job.result()
    uuid = None
    for row in results:
        uuid = row.uid
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    return uuid

def update_user_request(user_request):
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    update = pg.update_user_request(user_request)
    return update

def get_task_names(job_type):
    """Returns a list of task names for active tasks for a given type"""
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    try:
        task_names_list = pg.list_task_names_by_type(job_type)
        logger.info(f"Returning task names '{task_names_list}'")
        return task_names_list
    except Exception as e:
        logger.info(f"Error returning task names: {str(e)}")
        return None

def get_task(task_name):
    """Returns a task object"""
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    try:
        task_obj = pg.get_task_by_name(task_name)
        logger.info(f"Returning task '{task_name}'")
        return task_obj
    except Exception as e:
        logger.info(f"No task found with name '{task_name}': {str(e)}")
        return None

def create_task_instance(task, user_request):
    """Returns a task instance object"""
    logger.info(f"Create task instance with task id {task['id']} and user request id {user_request['id']}")
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    statsd_client = get_statsd_client(current_app.config.get('STATSD_HOST', None))
    try:
        task_instance = pg.create_task_instance(task, user_request)
        logger.info(f"Task instance created: {task_instance['id']}")
        if statsd_client:
            statsd_client.incr('api.create_task_instance.success')
        return task_instance
    except Exception as e:
        logger.info(f"Error inserting task instance: {e}")
        if statsd_client:
            statsd_client.incr('api.create_task_instance.fail')
        return None
