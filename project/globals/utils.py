import os
import sentry_sdk
import statsd

from google.cloud import storage

from project.globals import logger

def get_statsd_client(statsd_host):
    ENV = os.environ.get('ENV', 'staging')  # ENV passed in on the container build
    statsd_client=None
    try:
        statsd_client = statsd.StatsClient(host=statsd_host.split(':')[0], port=8125,
                prefix='privacy-request-management.%s' % ENV)
    except Exception as e:
        logger.info(f"Statsd client unavailable: {e}")
    return statsd_client

def get_sentry_client(sentrydsn, args):
    ENV = os.environ.get('ENV', 'staging')
    if ENV == 'production':
        try:
            sentry_client = sentry_sdk.init(dsn=sentrydsn)
        except Exception as e:
            logger.info(f"Sentry client unavailable: {e}")
            return None

    with sentry_client.configure_scope() as scope:
        scope.set_tag("environment", ENV)
        scope.set_tag("sysname", os.uname()[0])
        scope.set_tag("nodename", os.uname()[1])
        scope.set_tag("app", "data-privacy-request")

    return sentry_client
