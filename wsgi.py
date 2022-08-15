"""Application entry point."""
from app import init_app

app = init_app()

if __name__ == "__main__":
    app.secret_key = app.config['SECRET_KEY']
    app.run(host='0.0.0.0', debug=True, port=app.config["FORMIO_PORT"])
