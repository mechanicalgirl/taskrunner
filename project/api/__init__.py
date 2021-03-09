import json
import os
import sys

from flask import Flask
from flask_bootstrap import Bootstrap

# instantiate the extensions
bootstrap = Bootstrap()


def create_app(script_info=None):

    # instantiate the app
    app = Flask(__name__)

    # set config
    app_settings = os.getenv("APP_SETTINGS")
    app.config.from_object(app_settings)
    app.config.update(ENV = os.getenv('ENV'))
    f = open(os.getenv('APP_SECRETS'))
    secrets = json.load(f)
    app.config.update(
        PRIVACY_APP_DATABASE=secrets[app.env]['postgres'],
        STATSD_HOST=secrets[app.env]['statsd_endpoint']
    )

    # set up extensions
    bootstrap.init_app(app)

    from project.api.main import api_blueprint
    app.register_blueprint(api_blueprint)

    # shell context for flask cli
    app.shell_context_processor({"app": app})

    return app
