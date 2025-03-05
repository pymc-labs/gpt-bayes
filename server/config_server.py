import os
import logging
from google.cloud import logging as google_logging
from dotenv import load_dotenv

load_dotenv()

# Environment variables
API_KEY = os.environ.get('API_KEY', None)
MODEL_BUCKET = os.environ.get("MODEL_BUCKET", "bayes-gpt-models")
RUNNING_IN_GOOGLE_CLOUD = os.environ.get('RUNNING_IN_GOOGLE_CLOUD', 'False').lower() == 'true'
DATA_DIR = "/tmp/mmm_data"

# Cloud Run environment variables
CLOUD_RUN_URL = os.environ.get('CLOUD_RUN_URL', None)
def configure_app(app):
    """Configure Flask application"""
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost:6379/0",
            result_backend="redis://localhost:6379/0",
            worker_pool='threads',
            task_time_limit=600,
            broker_connection_retry=True,
            broker_connection_max_retries=0,
            task_serializer='dill',
            result_serializer='dill',
            accept_content=['dill']
        ),
    )

def configure_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger()

    if RUNNING_IN_GOOGLE_CLOUD:
        logging_client = google_logging.Client()
        cloud_handler = google_logging.handlers.CloudLoggingHandler(
            logging_client, 
            name='GPT-MMM'
        )
        logger.addHandler(cloud_handler)

def init_directories():
    """Initialize required directories"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.chmod(DATA_DIR, 0o777) 