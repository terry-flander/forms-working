import logging
import os

from psycopg2 import DataError

def setup_logger(name, log_file, level=logging.INFO):
    MESSAGE_FORMAT = os.environ.get('MESSAGE_FORMAT')
    DATE_STRFTIME_FORMAT = os.environ.get('DATE_STRFTIME_FORMAT')

    handler = logging.FileHandler(log_file)        
    formatter = logging.Formatter(MESSAGE_FORMAT, DATE_STRFTIME_FORMAT)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(level)
        logger.addHandler(handler)

    return logger

def build_error (field_name, message):
    return {
                "name": "ValidationError",
                "details": [ 
                    {
                        "message": message,
                        "type": "custom",
                        "level": "error",
                        "path": [field_name]
                    } 
                ]
            }        

