"""Initialize Flask app."""
from flask import Flask


def init_app():
    """Construct core Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    #app.config.from_object('config.Config')

    if app.config["ENV"] == "production":
        app.config.from_object("config.ProductionConfig")
    elif app.config["ENV"] == "staging":
        app.config.from_object("config.StagingConfig")
    else:
        app.config.from_object("config.DevelopmentConfig")  

    with app.app_context():
        # Import parts of our core Flask app
        from . import routes

        return app