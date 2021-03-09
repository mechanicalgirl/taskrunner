class BaseConfig(object):
    """Base configuration"""
    REDIS_URL = "redis://redis:6379/0"
    RQ_DASHBOARD_REDIS_URL = "redis://redis:6379/0"
    QUEUES = ['high', 'normal', 'low']
    # REDIS_HOST = 'redis'
    # REDIS_PORT = 6379
    STATSD_HOST = 'stats.voxops.net:8125'

class DevelopmentConfig(BaseConfig):
    """Development configuration (optional)"""
