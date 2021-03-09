from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    job_type = Column(String)
    name = Column(String)
    executor_class = Column(String)
    execution_time = Column(String)
    active = Column(String)
    created_on = Column(String)
    team = Column(String)
    team_contact = Column(String)
    description = Column(String)
    data_source = Column(String)
    timeout = Column(Integer)
    queue_name = Column(String)

    def __repr__(self):
       return "<Task(name='%s', job_type='%s', team='%s')>" % (self.name, self.job_type, self.team)

class TaskInstance(Base):
    __tablename__ = 'task_instance'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    request_id = Column(Integer)
    approved_by = Column(String)
    state = Column(String)
    message = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    duration = Column(Float)
    created_at = Column(String)
    cost = Column(Float)

    def __repr__(self):
       return "<TaskInstance(taskid='%s', userrequestid='%s')>" % (self.task_id, self.request_id)

class RequestType(Base):
    __tablename__ = 'request_type'

    id = Column(Integer, primary_key=True)
    request_type = Column(String)

    def __repr__(self):
       return "<RequestType(id='%s', type='%s')>" % (self.id, self.request_type)

class TaskType(Base):
    __tablename__ = 'task_type'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    request_type_id = Column(Integer)

    def __repr__(self):
       return "<TaskType(id='%s', task='%s', request_type='%s')>" % (self.id, self.task_id, self.request_type_id)

class UserRequest(Base):
    __tablename__ = 'user_request'

    id = Column(Integer, primary_key=True)
    created_at = Column(String)
    email = Column(String)
    request_date = Column(String)
    request_type = Column(String)
    request_meta = Column(String)
    chorus_user_id = Column(String)
    chorus_username = Column(String)
    chorus_author = Column(String)
    chorus_community = Column(String)
    notes = Column(String)
    deadline_date = Column(String)
    complete_date = Column(String)

    def __repr__(self):
       return "<UserRequest(request_type='%s', created_at='%s')>" % (self.request_type, self.created_at)

# These tables may not stay around - I'm trying to figure out the most efficient way to store
# db connections, but it's possible that there won't be any need for sources shared across
# multiple jobs. These are borrowed from the Maestro connection structure:
class DbSource(Base):
    __tablename__ = 'dbs'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    connect_str = Column(String)
    secret = Column(String)
    driver = Column(String)

    def __repr__(self):
       return "<DbSource(name='%s', driver='%s')>" % (self.name, self.driver)

class BigQueryConf(Base):
    __tablename__ = 'bq_conf'

    id = Column(Integer, primary_key=True)
    project_id = Column(String)
    service_account = Column(String)
    private_key_id = Column(String)
    key = Column(String)

    def __repr__(self):
       return "<BigQueryConf(project_id='%s')>" % (self.project_id)
