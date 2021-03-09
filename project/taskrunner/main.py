from datetime import datetime
import os
import sys
import time

import redis
from rq import Queue, Connection
from flask import Blueprint, jsonify, request, current_app

from project.globals.database import Database
from project.globals.utils import get_statsd_client
from project.globals import logger

# imports of new task classes to be added here
from project.taskrunner.tasks import TestTask, TestAccessTask, TestTaskScheduled
from project.taskrunner.tasks import PhonographDeleteTask, PhonographExtractTask
from project.taskrunner.tasks import EntriesNullTask, OwnerNullTask, GADeletionTask


taskrunner_blueprint = Blueprint("taskrunner", __name__,)

@taskrunner_blueprint.route("/task/<task_instance_id>", methods=["POST"])
def run_task(task_instance_id):
    # curl -X POST http://localhost:5004/task/13

    task_obj = get_task_instance(task_instance_id)
    task_setup = eval(task_obj['task']['executor_class'])
    response_object = {
        "state": '',
        "start_time": "",
        "end_time": "",
        "task": task_obj['task']['executor_class'],
        "data": {
            "task_instance_id": task_instance_id,
            "task": task_obj['task']['executor_class']
        }
    }

    # Bypass the Redis queue if the instance has already been run successfully
    # (allows retries on failed instances)
    if task_obj['task_instance']['state'] == 'success':
        response_object['state'] = task_obj['task_instance']['state']
        response_object['data']['error'] = f"This task was already completed on {task_obj['task_instance']['end_date']}"
        return jsonify(response_object), 200

    try:
        with Connection(redis.from_url(current_app.config["RQ_DASHBOARD_REDIS_URL"])):
            ## TODO: queue name (as an indicator of priority) can be added to the task object, with a default of 'low'
            q = Queue('low', is_async=True)
            # note: is_async=False bypasses workers for testing: https://python-rq.org/docs/#bypassing-workers

            """
            # This is still a little buggy, revisit later
            # if any phonograph delete job is already in the queue, drop this one - they cannot run concurrently
            for j in q.jobs:
                if j.kwargs['task']['executor_class'] == 'PhonographDeleteTask':
                    response_object['data']['result'] = 'Phonograph Delete tasks should not run concurrently - please try this task again later.'
                    return jsonify(response_object), 200
            """

            timeout = task_obj['task'].get('timeout', None)
            if not timeout:
                timeout = 120

            job = q.enqueue(task_setup().run, kwargs=task_obj, job_timeout=timeout)
            time.sleep(5)
            start_time = datetime.now()

            if job.is_queued:
                logger.info(f"Job ID {job.id} for {job.func_name} enqueued at {job.enqueued_at}")
                count=0
                while job.result==None and count <= timeout:
                    time.sleep(5)
                    count += 5
            if job.result:
                if job.result['status'] == 200:
                    response_object['state'] = "success"
                    response_object['data']['result'] = job.result['message']
                else:
                    response_object['state'] = "fail"
                    response_object['data']['error'] = job.result['message']
            else:
                response_object['state'] = "fail"
                response_object['data']['error'] = "No job result"

            end_time = datetime.now()
            response_object['start_time'] = start_time.strftime("%Y-%m-%d %H:%M:%S")
            response_object['end_time'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
            response_object['duration'] = (end_time-start_time).total_seconds()
            response_object['cost'] = job.result['cost']
    except Exception as e:
        response_object['state'] = "fail"
        response_object['data']['error'] = str(e)

    # leave our test class/task instance always active:
    if 'test' in task_obj['task']['executor_class'].lower():
        response_object['state'] = "active"

    # When the task instance is done, save its new state to the database
    update_task_instance(task_instance_id, response_object)

    statsd_client = get_statsd_client(current_app.config.get('STATSD_HOST', None))
    if statsd_client:
        statsd_client.incr(f"task.execute.{task_setup}.{response_object['state']}")

    return jsonify(response_object), 200

def get_task_instance(task_instance_id):
    """
    Find user and task metadata based on the instance id
    (used to build the redis message, this request would come from the dashboard)
    """
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])

    try:
        task_instance = pg.get_task_instance_by_id(task_instance_id)
        task_id = task_instance['task_id']
        request_id = task_instance['request_id']
    except Exception as e:
        raise Exception(f"Error retrieving task instance {task_instance_id}: {e}")

    try:
        task = pg.get_task_by_id(task_id)
    except Exception as e:
        raise Exception(f"Error retrieving task {task_id}: {e}")
    try:
        user_request = pg.get_user_request_by_id(request_id)
    except Exception as e:
        raise Exception(f"Error retrieving request {request_id}: {e}")

    return {'task': task, 'user_request': user_request, 'task_instance': task_instance}

def update_task_instance(task_instance_id, response):
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    try:
        task_instance = pg.update_task_instance_by_id(task_instance_id, response)
    except Exception as e:
        raise Exception(f"Error updating task instance {task_instance_id}: {e}")
        return False
    return True
