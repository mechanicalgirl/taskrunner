from flask_wtf import FlaskForm
from wtforms import TextField, TextAreaField, SelectField, BooleanField, IntegerField, DateField
from wtforms import validators

class TaskForm(FlaskForm):
    active = BooleanField(u'Active')
    job_type = SelectField(u'Job Type', choices=['access', 'deletion'], validators=[validators.Required("Please select a Job Type.")])
    name = TextField(u'Name', validators=[validators.Required("Please enter a task name.")])
    description = TextAreaField(u'Description')
    executor_class = TextField(u'Class Name', validators=[validators.Required("Please enter a class name.")])
    execution_time= TextField(u'Execution Time (UTC) (HH:MM:SS)')
    team = TextField(u'Team')
    team_contact = TextField(u'Team Contact')
    timeout = IntegerField(u'Timeout (optional, in seconds)', default=120)

class RequestForm(FlaskForm):
    email = TextField(u'Email Address', validators=[validators.Required("Please enter an email address.")])
    request_id = TextField('Request Id')
    request_type = SelectField(u'Request Type', choices=['Delete', 'Data Extract'], validators=[validators.Required("Please select a Request Type.")])
    chorus_user_id = IntegerField(u'Chorus User Id')
    chorus_username = TextField(u'Chorus Username')
    chorus_author = BooleanField(u'Chorus Author')
    request_date = DateField('Request Date (YYYY-MM-DD)', format='%Y-%m-%d', validators=(validators.Optional(),))
    request_due_date = DateField('Due Date (YYYY-MM-DD)', format='%Y-%m-%d', validators=(validators.Optional(),))
    gdpr_identifier = TextField(u'GDPR Identifier')
    ccpa_identifier = TextField(u'CCPA Identifier')
    uuid = TextField(u'Vox UUID')
    suid = TextField(u'Vox SUID')
    ga_cid = TextField(u'GA CID')
    notes = TextAreaField(u'Notes')
