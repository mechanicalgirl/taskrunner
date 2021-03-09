class BaseConfig(object):
    """Base configuration"""
    STATSD_HOST = 'stats.voxops.net:8125'

class DevelopmentConfig(BaseConfig):
    """Development configuration (optional)"""
