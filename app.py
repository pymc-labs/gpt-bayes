import json
from flask import Flask, request, jsonify
from celery import Celery, Task
from kombu import serialization

import pandas as pd
import arviz as az
from pymc_marketing.mmm import (
    GeometricAdstock,
    LogisticSaturation,
    MMM,
)

import logging

import dill
import os
import io

from functools import wraps

__version__ = "0.4"

API_KEY = os.environ.get('API_KEY', None)

running_in_google_cloud = os.environ.get('RUNNING_IN_GOOGLE_CLOUD', 'False').lower() == 'true'

# Configure standard logging
# Configure logging at the start of your app
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see debug messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

if running_in_google_cloud:
    # Configure Google Cloud Logging only if running in Google Cloud
    from google.cloud import logging as google_logging

    # Instantiates a Google Cloud logging client
    logging_client = google_logging.Client()

    # The name of the log to write to
    log_name = 'GPT-MMM'

    # Sets up Google Cloud logging
    cloud_handler = google_logging.handlers.CloudLoggingHandler(logging_client, name=log_name)
    logger.addHandler(cloud_handler)
else:
    # Additional local logging configuration (if needed)
    # For example, you can set a file handler or a stream handler for local logging
    pass
    # from celery.utils.log import get_task_logger
    # logging = get_task_logger(__name__)

# Register dill as the serialization method for Celery
serialization.register(
    name = 'dill',
    encoder = dill.dumps,
    decoder = dill.loads,
    content_type='application/octet-stream'
)

# Create module-level Celery instance
celery = Celery(
    "app",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskTask
    celery.config_from_object(app.config["CELERY"])
    app.extensions["celery"] = celery
    return celery

# Initialize Flask app
app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://localhost:6379/0",
        result_backend="redis://localhost:6379/0",
        worker_pool='threads',
        task_time_limit=600,
        broker_connection_retry=True,
        broker_connection_max_retries=0,  # Retry forever
        task_serializer='dill',
        result_serializer='dill',
        accept_content=['dill']
    ),
)
celery_app = celery_init_app(app)

# Create a data directory if it doesn't exist
DATA_DIR = "/tmp/mmm_data"
os.makedirs(DATA_DIR, exist_ok=True)
# Ensure proper permissions (readable/writable by all users)
os.chmod(DATA_DIR, 0o777)


@celery.task(bind=True)
def run_mmm_task(self, data):
    """Run Marketing Mix Model analysis task.
    
    Args:
        data (dict): Input data containing DataFrame and model parameters
    Returns:
        dict: Model summary statistics or error message
    """
    try:
        logging.info("Starting run_mmm_task here!!")
        
        # Use the dedicated data directory
        data_file = os.path.join(DATA_DIR, f"data_{self.request.id}.pkl")
        
        # Save the data to file
        with open(data_file, "wb") as f:
            dill.dump(data, f)
        
        # Ensure the file is readable/writable
        os.chmod(data_file, 0o666)

        try:
            file_refs = data.get("openaiFileIdRefs", [])
            if len(file_refs) == 0:
                logging.info("No file references found")
                raise ValueError("No file references found")
            else:
                download_url = file_refs[0].get("download_link", "") # TODO: handle multiple files
                logging.info("Downloading data from %s", download_url)
                
                # Add headers to the request
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'text/csv'
                }
                
                try:
                    # Use requests library for better control over the HTTP request
                    import requests
                    response = requests.get(download_url, headers=headers)
                    response.raise_for_status()  # Raise an exception for bad status codes
                    
                    # Read CSV from the response content
                    df = pd.read_csv(io.StringIO(response.text))
                    logging.info("Data downloaded successfully")
                except requests.exceptions.RequestException as e:
                    logging.error("Failed to download file: %s", str(e), exc_info=True)
                    raise ValueError(f"Failed to download file: {str(e)}")

                logging.info("Saving data to file")
                file_name = file_refs[0].get("name", "")
                file_path = os.path.join(DATA_DIR, file_name)
                df.to_csv(file_path, index=False)
                logging.info("Data saved to file %s", file_path)

        except Exception as e:
            logging.error("Error reading data attempting to read CSV: %s", str(e), exc_info=True)
            raise e

        logging.info("DataFrame loaded with shape=%s and columns=%s", df.shape, df.columns)
        logging.info("First 5 rows:\n%s", df.head(5))

        # Check if DataFrame has at least 15 rows
        if len(df) < 15: raise ValueError(f"DataFrame must have at least 15 rows for reliable model fitting. Current shape: {df.shape}")

        # Extract optional parameters from 'data'
        date_column = data.get('date_column', 'date')
        channel_columns = data.get('channel_columns', [])
        adstock_max_lag = data.get('adstock_max_lag', 8)
        yearly_seasonality = data.get('yearly_seasonality', 2)
        control_columns = data.get('control_columns', None)
        y_column = data.get('y_column', 'y')
        logging.debug("Parameters extracted: date_column=%s, channel_columns=%s, adstock_max_lag=%d, yearly_seasonality=%d, control_columns=%s",
                     date_column, channel_columns, adstock_max_lag, yearly_seasonality, control_columns)

        def is_valid_dates(df, column):
            return pd.to_datetime(df[column], format='%Y-%m-%d', errors='coerce').notna().all()

        if not is_valid_dates(df, date_column):
            raise ValueError(f"Date column must be in YYYY-MM-DD format (e.g. 2023-12-31). Found values like: {df[date_column].iloc[0]} with dtype: {df[date_column].dtype}")

        logging.debug("Creating MMM model")
        mmm = MMM(
            adstock=GeometricAdstock(l_max=adstock_max_lag),
            saturation=LogisticSaturation(),
            date_column=date_column,
            channel_columns=channel_columns,
            control_columns=control_columns,
            yearly_seasonality=yearly_seasonality,
        )
        logging.info("MMM model defined.")

        # Ensure date_week is in datetime format
        df[date_column] = pd.to_datetime(df[date_column])
        
        
        # X = df.drop(y_column, axis=1).astype(float)
        X = df.drop(y_column, axis=1)
        y = df[y_column].astype(float)
            
        mmm.fit(X, y)
        logging.info("Model fitting completed.")
        logging.info("run_mmm_task completed successfully.")

        return mmm
    
    except Exception as e:
        logging.error("run_mmm_task failed: %s\nJSON data: %s", str(e), data, exc_info=True)
        return {"status": "failed", "error": str(e)}
    
def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if api_key and api_key == API_KEY:
            return func(*args, **kwargs)
        else:
            return jsonify({"message": "Unauthorized"}), 401
    return decorated_function

@app.route('/run_mmm_async', methods=['POST'])
@require_api_key
def run_mmm_async():
    try:
        logging.info("Received request to run_mmm_async")
        data = request.get_json()
        logging.debug("run_mmm_async request data: %s", data)

        logging.info("checking that the data has file_refs: %s", data)
        if ("openaiFileIdRefs" not in data) or (len(data["openaiFileIdRefs"]) == 0): # TODO: do a more thorough schema check here
            logging.error("Data does not have openaiFileIdRefs")
            return jsonify({"error": "Request must include openaiFileIdRefs"}), 400
        else:
            logging.info("Data has openaiFileIdRefs")

        task = run_mmm_task.apply_async(args=[data])
        logging.info("Task submitted with ID: %s", task.id)

        return jsonify({"task_id": task.id})
    except Exception as e:
        logging.error("Error in run_mmm_async: %s", str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500
    

@app.route('/get_task_status', methods=['GET'])
@require_api_key
def get_task_status():
    task_id = request.args.get('task_id')
    task = run_mmm_task.AsyncResult(task_id)
    return jsonify({"status": task.state})

def check_task_status(f):
    @wraps(f)  # Preserve function metadata
    def wrapper(*args, **kwargs):
        try:
            task_id = request.args.get('task_id')  # Simplify task_id extraction
            if not task_id:
                return jsonify({"status": "failure", "error": "No task_id provided"}), 400

            logging.info("Checking task status with task_id: %s", task_id)

            task = run_mmm_task.AsyncResult(task_id)
            if task.state == 'PENDING':
                logging.info("Task %s is still pending.", task_id)
                return jsonify({"status": "pending"})
            elif task.state == 'FAILURE':
                logging.error("Task %s failed.", task_id)
                return jsonify({"status": "failure", "error": str(task.info)})
            
            # If task completed successfully, proceed with the decorated function
            logging.info("Task %s completed successfully.", task_id)
            return f(*args, **kwargs)
            
        except Exception as e:
            logging.error("Error in check_task_status: %s", str(e), exc_info=True)
            return jsonify({"status": "failure", "error": str(e)}), 500
    
    return wrapper

@app.route('/get_summary_statistics', methods=['GET'])
@require_api_key
@check_task_status
def get_summary_statistics():
    try:
        task_id = request.args.get('task_id')
        task = run_mmm_task.AsyncResult(task_id)
        mmm = task.result
        logging.info("MMM model: %s", mmm)

        # Extract and return summary statistics
        summary = az.summary(mmm.fit_result)
        
        # Filter only the most important statistics
        important_params = summary[summary.index.str.contains('alpha|beta|sigma|intercept|lam|gamma_control', case=False)]
        # Limit decimal places and convert to more compact format
        important_params = important_params.round(5)
        
        summary_json = important_params.to_json(orient="split", double_precision=5)
        logging.info("Summary statistics extracted.")
        logging.info("summary_json=%s", summary_json)

        return jsonify({"status": "completed", "summary": summary_json})
    except Exception as e:
        logging.error("Error in extract_summary_statistics: %s", str(e), exc_info=True)
        return jsonify({"status": "failure", "error": str(e)}), 500

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--port', default=5001, type=int)
    args = parser.parse_args()
    
    # Update this line to use args.port instead of hardcoded 8080
    app.run(host='0.0.0.0', port=args.port, debug=False)