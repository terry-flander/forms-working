import psycopg2
import psycopg2.extras
import logging
import sys
import os

from app.lib.util import setup_logger
debug_logger = setup_logger('debug', 'tmp/app_info.log', logging.DEBUG)
app_logger = setup_logger('info', 'tmp/app_info.log', logging.INFO)

class Timescale:
    def __init__(self):
        pass

    def connect(self, connection):
        try:
            keepalive_kwargs = {
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 5,
                "keepalives_count": 5,
            }
            self.connection = psycopg2.connect(connection, **keepalive_kwargs)
            self.connection.set_session(readonly=False)
            return 'ok'
        except Exception as ex:
            app_logger.error(ex)
            return str(ex)

    def disconnect(self):
        try:
            self.connection.close()
            self.connection = None
        except Exception as ex:
            app_logger.error(ex)
            return 'ok'

    def update(self, query, commit=True):
        try:
            if query is not None:
                cur = self.connection.cursor()
                cur.execute(query)
            if commit:
                self.connection.commit()
                cur.close()
            return "ok"
        except Exception as ex:
            app_logger.error(ex)
            return str(ex)
