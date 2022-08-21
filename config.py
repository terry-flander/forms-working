class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = "B\xb2?.\xdf\x9f\xa7m\xf8\x8a%,\xf7\xc4\xfa\x91"

    DB_NAME = "production-db"
    DB_USERNAME = "admin"
    DB_PASSWORD = "example"

    FORMIO_PORT = 8080

    IMAGE_UPLOADS = "/home/username/app/app/static/images/uploads"

    SESSION_COOKIE_SECURE = True

    DATE_STRFTIME_FORMAT = "%d-%b-%y %H:%M:%S"
    MESSAGE_FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    LOGGING_LEVEL = 'INFO'

    FORMIO_URL = ''
    OPS_PORTAL_URL = ''

    ADMIN_USER = 'admin@example.com'
    ADMIN_PASSWORD = 'CHANGEME'

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

    DB_NAME = "development-db"
    DB_USERNAME = "admin"
    DB_PASSWORD = "example"

    IMAGE_UPLOADS = "/home/username/projects/my_app/app/static/images/uploads"

    SESSION_COOKIE_SECURE = False
    FORMIO_PORT = 8010
    FORMIO_URL = '192.168.1.5:3001'
    OPS_PORTAL_URL = 'http://192.168.1.5:8000'

    MESSAGE_FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    LOGGING_LEVEL = 'DEBUG'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

class StagingConfig(Config):
    TESTING = True

    DB_NAME = "development-db"
    DB_USERNAME = "admin"
    DB_PASSWORD = "example"

    FORMIO_PORT = 8010

    SESSION_COOKIE_SECURE = False