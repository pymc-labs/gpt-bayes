import json
import os
import logging
from flask import Flask
from config_server import configure_app, configure_logging, init_directories
from celery_setup import setup_celery
from routes import register_routes

__version__ = "0.5"

# Create and configure the Flask app at module level
app = Flask(__name__)
configure_app(app)
configure_logging()
celery = setup_celery(app)
init_directories()
register_routes(app)

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--port', default=8080, type=int)
    args = parser.parse_args()
    
    app.run(host='0.0.0.0', port=args.port, debug=False)