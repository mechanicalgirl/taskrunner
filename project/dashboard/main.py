from datetime import datetime
import json
import requests
import sys

from flask import Blueprint, jsonify, current_app
from flask import render_template, request, redirect
from flask import flash
from flask_login import current_user, login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient

from project.globals.database import Database
from project.globals.utils import get_statsd_client
from project.globals import logger

from project.dashboard.forms import TaskForm, RequestForm
from project.dashboard.user import User


dashboard_blueprint = Blueprint("dashboard", __name__,)

@dashboard_blueprint.route("/", methods=["GET"])
def home():
    """List all open/active user requests"""
    # logger.info(f"LOGIN MANAGER {dir(current_app.login_manager)}")
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    ## TODO: implement Google login and track here
    statsd_client = get_statsd_client(current_app.config.get('STATSD_HOST', None))
    if statsd_client:
        statsd_client.incr(f"dashboard.home")

    unsorted_requests = get_active_user_requests()
    requests = sorted(unsorted_requests, key = lambda i: i['id'], reverse=True)

    return render_template('index.html', **locals())

@dashboard_blueprint.route("/completed/", methods=["GET"])
def completed():
    """List all closed user requests"""
    # logger.info(f"LOGIN MANAGER {dir(current_app.login_manager)}")
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    ## TODO: implement Google login and track here
    statsd_client = get_statsd_client(current_app.config.get('STATSD_HOST', None))
    if statsd_client:
        statsd_client.incr(f"dashboard.completed")

    unsorted_requests = get_completed_user_requests()
    requests = sorted(unsorted_requests, key = lambda i: i['id'], reverse=True)

    return render_template('complete.html', **locals())

@dashboard_blueprint.route("/user/<user_request_id>", methods=["GET"])
def user(user_request_id):
    """Look at all the task instances associated with a user id"""
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    user_task_instances = get_task_instances(user_request_id)
    user_request = user_task_instances['user_request']
    task_instances = user_task_instances['task_instances']

    return render_template('user.html', **locals())

@dashboard_blueprint.route("/user/taskinstance/<task_instance_id>/user_request/<user_request_id>", methods=["GET"])
def trigger_task(task_instance_id, user_request_id):
    """
    Trigger a task by passing the task_instance_id to the taskrunner
    """
    logger.info(f"Task instance id: {task_instance_id}")

    url = f"http://localhost:5004/taskrunner/task/{task_instance_id}"
    r = requests.post(url)

    logger.info(f"Taskrunner response: {r} {r.json()} {r.text}")

    flash(f"Taskrunner Response: {r}")
    return redirect(f'/user/{user_request_id}')



@dashboard_blueprint.route("/admin/", methods=["GET"])
def admin():
    """admin menu page"""
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    return render_template('admin.html', **locals())

@dashboard_blueprint.route("/admin/tasks/", methods=["GET", "POST"])
def list_tasks():
    """List all tasks"""
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    tasks = list_all_tasks()
    return render_template('admin_tasks.html', **locals())

@dashboard_blueprint.route("/admin/addtask/", methods=["GET", "POST"])
def add_task():
    """Add a new task"""
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    form = TaskForm()
    if form.validate_on_submit():
        try:
            pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
            new_task = pg.insert_task(form.data)
            logger.info(f"New task {new_task}: {form.data}")
            flash(f"New task {new_task}: {form.data}")
        except Exception as e:
            logger.info(f"Error: {e}")
            flash(e)
        return redirect('/admin/tasks/')
    return render_template('admin_add_task.html', **locals())

@dashboard_blueprint.route("/admin/edittask/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    """Edit an existing task"""
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    task_obj = pg.get_task_by_id(task_id)
    if not task_obj:
        return redirect('/admin/tasks/')

    form = TaskForm()
    if request.method == 'GET':
        form.active.data = task_obj['active']
        form.job_type.data = task_obj['job_type']
        form.name.data = task_obj['name']
        form.description.data = task_obj['description']
        form.executor_class.data = task_obj['executor_class']
        form.team.data = task_obj['team']
        form.team_contact.data = task_obj['team_contact']
        form.timeout.data = task_obj['timeout']
    if form.validate_on_submit():
        try:
            updated_task = pg.update_task(task_id, form.data)
            logger.info(f"Updated task {task_id}: {form.data}")
            flash(f"Updated task {task_id}: {form.data}")
        except Exception as e:
            logger.info(f"Error: {e}")
            flash(e)
        return redirect('/admin/tasks/')
    return render_template('admin_edit_task.html', **locals())

@dashboard_blueprint.route("/admin/addrequest/", methods=["GET", "POST"])
def add_user_request_json():
    """
    User requests added via JSON object
    """
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    ## TODO: flash message

    return render_template('admin_add_user.html', **locals())

@dashboard_blueprint.route("/admin/addrequestform/", methods=["GET", "POST"])
def add_user_request_form():
    """
    Simplified form to add user request instead of going
    through the API (this is temporary - user requests should
    be posted to the API via a contact form)
    """
    if not current_user.is_authenticated and current_app.env != 'local':
        return render_template('login.html', **locals())
    if current_app.env == 'local':
        local_user = True

    form = RequestForm()
    if form.validate_on_submit():
        logger.info(f"Received user request {form.data}")
        # package as JSON and post to the API
        post_data = form.data
        post_data['request_date'] = form.data['request_date'].strftime("%Y-%m-%d %H:%M:%S")
        post_data['request_meta'] = {
            "identifiers": {
              "gdpr_identifier": form.data['gdpr_identifier'],
              "ccpa_identifier": form.data['ccpa_identifier'],
              "uuid": form.data['uuid'],
              "suid": form.data['suid']
            },
            "details": form.data['notes']
        }
        url = 'http://api:5000/userrequest/'
        payload = json.dumps(post_data)
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
        r = requests.post(url, data=payload, headers=headers)
        logger.info(f"API Response: {r.content}")
        flash(f"API Response: {r.content}")
        return redirect('/')
    return render_template('admin_add_user_form.html', **locals())


def get_active_user_requests():
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    try:
        request_list = pg.get_active_user_requests()
    except Exception as e:
        raise Exception(f"Error retrieving user requests: {e}")
    user_list = format_request_list(request_list)
    return user_list

def get_completed_user_requests():
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    try:
        request_list = pg.get_completed_user_requests()
    except Exception as e:
        raise Exception(f"Error retrieving user requests: {e}")
    user_list = format_request_list(request_list)
    return user_list

def format_request_list(request_list):
    user_list = []
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    for user in request_list:
        user = user._asdict()
        task_instances = pg.get_task_instances_by_request_id(user['id'])
        success = True
        task_states = []
        for t in task_instances:
            task_states.append(t['task_instance']['state'])
            if t['task_instance']['state'] != 'success':
                success = False
        user['states'] = sorted(task_states)
        if success and not user['complete_date']:
            user['complete_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pg.complete_user_request(user)
        else:
            # only uncompleted requests are returned here
            user_list.append(user)
    return user_list

def get_task_instances(user_request_id):
    """
    Find task instance metadata based on the user request id
    """
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])

    try:
        user_request = pg.get_user_request_by_id(user_request_id)
    except Exception as e:
        raise Exception(f"Error retrieving request {user_request_id}: {e}")

    try:
        task_instances = pg.get_task_instances_by_request_id(user_request_id)
    except Exception as e:
        raise Exception(f"Error retrieving task instances for {user_request_id}: {e}")

    for t in task_instances:
        task_id = t['task_instance']['task_id']
        try:
            task = pg.get_task_by_id(task_id)
            t['task'] = task
        except Exception as e:
            raise Exception(f"Error retrieving task {task_id}: {e}")

    # this is temporary - admin user should be able to sort manually
    task_instances = sorted(task_instances, key = lambda i: i['task_instance']['task_id'])
    return {'user_request': user_request, 'task_instances': task_instances}

def list_all_tasks():
    pg = Database(current_app.config['PRIVACY_APP_DATABASE'])
    try:
        tasks = pg.list_all_tasks()
    except Exception as e:
        raise Exception(f"Error retrieving tasks: {e}")

    return tasks


## login methods
def get_google_provider_cfg():
    DISCOVERY_URL = current_app.config.get('DISCOVERY_URL', None)
    return requests.get(DISCOVERY_URL).json()

# arrive at this route via the button in the login template
@dashboard_blueprint.route("/login", methods=['GET'])
def login():
    REDIRECT_URI = current_app.config.get('REDIRECT_URI', None)
    CLIENT_ID = current_app.config.get('CLIENT_ID', None)

    # OAuth 2 bqclient.setup
    authclient = WebApplicationClient(CLIENT_ID)

    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    base_url = request.base_url
    if base_url.startswith('http:'):
        base_url = base_url.replace('http:', 'https:')
    request_uri = authclient.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=base_url + "/callback",
        # redirect_uri=REDIRECT_URI,
        scope=["openid", "email", "profile"],
    )

    # redirect to the Google auth url, which then routes to the callback
    return redirect(request_uri)

@dashboard_blueprint.route("/login/callback", methods=['GET', 'POST'])
def callback():
    CLIENT_ID = current_app.config.get('CLIENT_ID', None)
    CLIENT_SECRET = current_app.config.get('CLIENT_SECRET', None)

    # OAuth 2 bqclient.setup
    authclient = WebApplicationClient(CLIENT_ID)

    # Get authorization code Google sent back to you
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # prepare and send a request to get tokens
    url = request.url
    base_url = request.base_url
    if url.startswith('http:'):
        url = url.replace('http:', 'https:')
    if base_url.startswith('http:'):
        base_url = base_url.replace('http:', 'https:')
    token_url, headers, body = authclient.prepare_token_request(
        token_endpoint,
        authorization_response=url,
        redirect_url=base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(CLIENT_ID, CLIENT_SECRET),
    )

    # parse the tokens
    authclient.parse_request_body_response(json.dumps(token_response.json()))

    # get the user's profile information
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = authclient.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # make sure the user is verified
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    user = User(
        id_=unique_id, name=users_name, email=users_email
    )
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email)

    login_user(user)
    logger.info(f"Logging in: {users_email}")

    table = 'logins_%s' % app.env
    rows = [[(datetime.now()).strftime("%Y-%m-%d %H:%M:%S"), unique_id]]

    # replace with insert into the main db
    # login_inserts = dd_inserts(table, rows)

    redir_url = base_url.replace("/login/callback", "")
    return redirect(redir_url)

@dashboard_blueprint.route("/logout")
@login_required
def logout():
    logger.info(f"Logging out: %s" % current_user.email)
    logout_user()
    redir_url = request.base_url.replace("/logout", "")
    return redirect(redir_url)
