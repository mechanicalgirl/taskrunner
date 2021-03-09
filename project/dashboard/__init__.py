import json
import os
import sys

from flask import Flask
from flask_login import LoginManager
import rq_dashboard

# instantiate the extensions
login_manager = LoginManager()


def create_app(script_info=None):

    # instantiate the app
    app = Flask(__name__)
    ## this key is not used for anything secure, it's just a value required by Flask to do message flashing:
    app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

    # set config
    app.config.from_object(rq_dashboard.default_settings)
    # another option: app.config.from_pyfile('config.py')
    app.config.update(ENV = os.getenv('ENV'))
    f = open(os.getenv('APP_SECRETS'))
    secrets = json.load(f)
    app.config.update(
        PRIVACY_APP_DATABASE=secrets[app.env]['postgres'],
        STATSD_HOST=secrets[app.env]['statsd_endpoint'],
        WTF_CSRF_ENABLED = False,
        # WTF_CSRF_SECRET_KEY = 'a random string'
        ## for Google log in:
        # CLIENT_ID = secrets[app.env]['client_id'],
        # CLIENT_SECRET = secrets[app.env]['client_secret'],
        # DISCOVERY_URL = secrets[app.env]['google_discovery_url'],
        # REDIRECT_URI = secrets[app.env]['redirect_uris'][0]
    )

    # set up extensions
    login_manager.init_app(app)

    from project.dashboard.main import dashboard_blueprint
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix='/rqdashboard')

    # shell context for flask cli
    app.shell_context_processor({"app": app})

    return app
