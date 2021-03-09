import datetime
import json
from json import JSONEncoder
import sys

from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from project.globals import logger


class DateTimeEncoder(JSONEncoder):
    # other usage: json.dumps(user, indent=4, cls=DateTimeEncoder)
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()

class Database(object):
    """
    PostgreSQL database utility methods
    """

    def __init__(self, engine_name):
        Session = sessionmaker()
        self.engine = create_engine(engine_name)
        Session.configure(bind=self.engine)
        self.metadata = MetaData(bind=self.engine)
        self.session = Session()

    def create_user_request(self, user_request):
        """Use incoming request json to create a user request instance, return the id"""
        request_meta = json.dumps(user_request['request_meta'])
        USER_REQUEST = """
          INSERT INTO user_request (created_at, email, request_type, request_meta,
              chorus_user_id, chorus_community, deadline_date, request_date)
          VALUES (:created_at, :email, :request_type, :request_meta,
              :chorus_user_id, :chorus_community, :deadline_date, :request_date)
          ON CONFLICT ON CONSTRAINT unique_request
          DO NOTHING
          RETURNING id
        """
        try:
            result = self.engine.execute(text(USER_REQUEST),{
                'created_at': user_request['created_at'],
                'email': user_request['email'],
                'request_type': user_request['request_type'],
                'request_meta': request_meta,
                'chorus_user_id': user_request['chorus_user_id'],
                'chorus_community': user_request.get('chorus_community', ''),
                'deadline_date': user_request['deadline_date'],
                'request_date': user_request['request_date']
            })
            request_instance = result.fetchone()[0]
            return request_instance
        except Exception as e:
            logger.info(f"Insert error: {e}")
            logger.info(f"Error: request for {user_request['email']} already exists")
            return False

    def get_user_request_by_id(self, id):
        """Find a user request where user_request.id maps to the --requestid value passed in on the request"""
        user_request_table = Table('user_request', self.metadata, autoload=True)
        try:
            u = self.session.query(user_request_table).filter(user_request_table.c.id==id).one()
            raw_request = u._asdict()
            user_request = json.loads(DateTimeEncoder().encode(raw_request))
            return user_request
        except Exception as e:
            logger.info(f"Error retrieving request {id}: {e}")
            return False

    def get_active_user_requests(self):
        """Find all active user requests"""
        user_request_table = Table('user_request', self.metadata, autoload=True)
        try:
            u = self.session.query(user_request_table).filter(user_request_table.c.complete_date == None).all()
            return u
        except Exception as e:
            logger.info(f"Error retrieving active user requests: {e}")
            return False

    def get_completed_user_requests(self):
        """Find all completed user requests"""
        user_request_table = Table('user_request', self.metadata, autoload=True)
        try:
            u = self.session.query(user_request_table).filter(user_request_table.c.complete_date != None).all()
            return u
        except Exception as e:
            logger.info(f"Error retrieving completed user requests: {e}")
            return False

    def update_user_request(self, request):
        """
        Add values to user request metadata based on task instance results
        """
        # enforce a default arg type, or check incoming?
        meta = json.dumps(request['request_meta'])
        USER_META = """
          UPDATE user_request
          SET
            request_meta = :metadata,
            notes = :notes
          WHERE id = :id
          RETURNING id
        """
        try:
            result = self.engine.execute(text(USER_META),{'metadata': meta, 'notes': request['notes'], 'id': request['id']})
        except Exception as e:
            logger.info(f"Error updating user request {request['id']}: {e}")
            return False
        return True

    def complete_user_request(self, user_request):
        """
        Add completion date to user request
        """
        USER_COMPLETE = """
          UPDATE user_request SET complete_date = :complete_date
          WHERE id = :id
          RETURNING id
        """
        try:
            result = self.engine.execute(text(USER_COMPLETE),{'complete_date': user_request['complete_date'], 'id': user_request['id']})
        except Exception as e:
            logger.info(f"Error updating user request {user_request['id']}: {e}")
            return False
        return True



    def get_task_by_name(self, task_name):
        """Find a task where task.name maps to the --task value passed in on the request"""
        task_table = Table('task', self.metadata, autoload=True)
        try:
            parent_task = self.session.query(task_table).filter(task_table.c.name==str(task_name)).one()
            task = parent_task._asdict()
            return task
        except Exception as e:
            logger.info(f"Error retrieving task {task_name}: {e}")
            return False

    def get_task_by_id(self, id):
        """Find a task where task.id maps to an optional --taskid value passed in on the request"""
        task_table = Table('task', self.metadata, autoload=True)
        try:
            parent_task = self.session.query(task_table).filter(task_table.c.id==id).one()
            task = parent_task._asdict()
            return task
        except Exception as e:
            logger.info(f"Error retrieving task {id}: {e}")
            return False

    def list_task_names_by_type(self, job_type):
        """Returns a list of task names for active tasks for a given type"""
        TASK_NAMES = """
            SELECT name 
            FROM task
            WHERE active IS true and job_type = :job_type
        """
        result = self.engine.execute(text(TASK_NAMES),{'job_type': job_type}).fetchall()
        task_names = [x[0] for x in result]
        return task_names

    def list_all_tasks(self):
        """For the dashboard admin"""
        task_table = Table('task', self.metadata, autoload=True)
        try:
            all_tasks = self.session.query(task_table).all()
            task_list = []
            for t in all_tasks:
                task_list.append(t._asdict())
            return task_list
        except Exception as e:
            logger.info(f"Error retrieving list of tasks: {e}")
            return False

    def insert_task(self, task_obj):
        """From the dashboard admin"""
        task_table = Table('task', self.metadata, autoload=True)
        ins = task_table.insert().values(
            job_type=task_obj['job_type'],
            name=task_obj['name'],
            description=task_obj['description'],
            executor_class=task_obj['executor_class'],
            execution_time=task_obj['execution_time'],
            team=task_obj['team'],
            team_contact=task_obj['team_contact'],
            timeout=task_obj['timeout'],
            created_on=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            active=True
        )
        try:
            result = self.engine.execute(ins)
            task_id = result.inserted_primary_key[0]
            return task_id
        except Exception as e:
            logger.info(f"Error inserting task: {e}")
            return False

    def update_task(self, task_id, task_obj):
        TASK = """
            UPDATE task
            SET job_type=:job_type, name=:name, description=:description,
                executor_class=:executor_class, execution_time=:execution_time,
                team=:team, team_contact=:team_contact, timeout=:timeout,
                active=:active
            WHERE task.id = :id
        """
        try:
            result = self.engine.execute(text(TASK),{
                'id': task_id,
                'job_type': task_obj['job_type'],
                'name': task_obj['name'],
                'description': task_obj['description'],
                'executor_class': task_obj['executor_class'],
                'execution_time': task_obj['execution_time'],
                'team': task_obj['team'],
                'team_contact': task_obj['team_contact'],
                'timeout': task_obj['timeout'],
                'active': task_obj['active']
            })
        except Exception as e:
            logger.info(f"Error updating task {task_id}: {e}")
            return False
        return True



    def create_task_instance(self, task, user_request):
        """Use task and request metadata to create a task instance"""
        TASK_INSTANCE = """
          INSERT INTO task_instance (task_id, request_id, approved_by, state, created_at)
          VALUES (:task_id, :request_id, :approved_by, :state, NOW())
          ON CONFLICT ON CONSTRAINT unique_task_request 
          DO UPDATE SET approved_by=EXCLUDED.approved_by
          RETURNING *
        """
        try:
            result = self.engine.execute(text(TASK_INSTANCE),{'task_id': task['id'],
                'request_id': user_request['id'],
                'approved_by': task['team_contact'],  # placeholder value
                'state': 'active'})                   # placeholder value
            task_instance = dict(result.fetchone().items())
            return task_instance
        except Exception as e:
            logger.info(f"Error creating task instance {task['name']}, {user_request['email']}: {e}")
            return False

    def get_task_instance_by_id(self, task_instance_id):
        """raw SQL example"""
        TASK_INSTANCE = """
            SELECT id, task_id, request_id, approved_by, state,
                message, start_date, end_date, duration
            FROM task_instance WHERE task_instance.id = :identifier
        """
        result = self.engine.execute(text(TASK_INSTANCE),{'identifier': task_instance_id}).fetchone()
        task_instance = dict(result.items())
        return task_instance

    def get_task_instance_by_task_id(self, task_id):
        TASK_INSTANCE = """
            SELECT id, task_id, request_id, approved_by, state,
                message, start_date, end_date, duration
            FROM task_instance WHERE task_instance.task_id = ':identifier'
        """
        result = self.engine.execute(text(TASK_INSTANCE),{'identifier': task_instance_id})
        task_instance = dict(result.fetchone().items())
        return task_instance

    def get_task_instances_by_request_id(self, request_id):
        TASK_INSTANCE = """
            SELECT id, task_id, request_id, approved_by, state,
                message, start_date, end_date, duration, cost
            FROM task_instance WHERE task_instance.request_id = :identifier
        """
        result = self.engine.execute(text(TASK_INSTANCE),{'identifier': request_id})
        task_instances = result.fetchall()
        task_instances_list = []
        for t in task_instances:
            task_instances_list.append({'task_instance': dict(t)})
        return task_instances_list

    def update_task_instance_by_id(self, task_instance_id, response):
        TASK_INSTANCE = """
            UPDATE task_instance
            SET state = :status, message = :message,
            start_date = :start_date, end_date = :end_date,
            duration = :duration, cost = :cost
            WHERE task_instance.id = :identifier
        """
        message = response.get('data', '').get('error', response.get('data', '').get('result', ''))
        cost = response.get('cost', 0)
        try:
            result = self.engine.execute(text(TASK_INSTANCE),{
                'identifier': task_instance_id,
                'status': response['state'],
                'message': message,
                'start_date': response['start_time'],
                'end_date': response['end_time'],
                'duration': response['duration'],
                'cost': cost
            })
        except Exception as e:
            logger.info(f"Error updating task instance {task_instance_id}: {e}")
            return False
        return True
