from flask import Flask, request, jsonify
from celery import Celery

import pandas as pd
import arviz as az

from pymc_marketing.mmm import (
    GeometricAdstock,
    LogisticSaturation,
    MMM,
)

import logging

import pickle
import os
import io


__version__ = "0.3"

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

# Initialize Celery

app = Flask(__name__)
app.config['broker_url'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['broker_url'])
celery.conf.update(app.config)
celery.conf.update(
    worker_pool='threads',  # Use prefork (multiprocessing)
    task_always_eager=False,  # Ensure tasks are not run locally by the worker that started them
    task_time_limit=600,  # Add 1-hour timeout
    broker_connection_retry_on_startup=True,  # Retry broker connection on startup
    worker_redirect_stdouts=False,  # Don't redirect stdout/stderr
    worker_redirect_stdouts_level='DEBUG',  # Log level for stdout/stderr
    broker_transport_options={
        'retry_on_timeout': True,
        'max_retries': 3,
    },
    redis_max_connections=10,
    broker_pool_limit=None,  # Disable connection pool size limit
)

# Add Redis error logging
logging.info("Initializing Celery with Redis backend")
try:
    celery.backend.client.ping()
    logging.info("Successfully connected to Redis backend")
except Exception as e:
    logging.error("Failed to connect to Redis: %s", str(e), exc_info=True)

logging.info("App started. Version: %s", __version__)

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
            pickle.dump(data, f)
        
        # Ensure the file is readable/writable
        os.chmod(data_file, 0o666)

        try:
            df = pd.read_json(io.StringIO(data["df"]), orient="split")
        except Exception as e:
            logging.info("Error reading JSON data attempting to read CSV: %s", str(e), exc_info=True)
            df = pd.read_csv(io.StringIO(data["df"]))            


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
        logging.debug("Parameters extracted: date_column=%s, channel_columns=%s, adstock_max_lag=%d, yearly_seasonality=%d, control_columns=%s",
                     date_column, channel_columns, adstock_max_lag, yearly_seasonality, control_columns)

        def is_valid_dates(df, column):
            return pd.to_datetime(df[column], format='%Y-%m-%d', errors='coerce').notna().all()

        if not is_valid_dates(df, date_column):
            raise ValueError(f"Date column must be in YYYY-MM-DD format (e.g. 2023-12-31). Found values like: {df[date_column].iloc[0]} with dtype: {df[date_column].dtype}")


        # Define and fit the MMM model
        # import ipdb; ipdb.set_trace()

        logging.debug("Creating MMM model")
        mmm = MMM(
            adstock=GeometricAdstock(l_max=int(adstock_max_lag)),
            saturation=LogisticSaturation(),
            date_column=date_column,
            channel_columns=channel_columns,
            control_columns=control_columns,
            yearly_seasonality=yearly_seasonality,
        )
        logging.info("MMM model defined.")
        
        X = df.drop('sales', axis=1)
        y = df['sales']

        logging.debug("Starting model fitting.")

        # mmm.fit(X, y, random_seed=42, cores=1)
        mmm.fit(X, y)
        logging.info("Model fitting completed.")
        
        # Extract and return summary statistics
        summary = az.summary(mmm.fit_result)
        
        # Filter only the most important statistics
        important_params = summary[summary.index.str.contains('alpha|beta|sigma|intercept|lam|gamma_control', case=False)]
        # Limit decimal places and convert to more compact format
        important_params = important_params.round(5)
        
        summary_json = important_params.to_json(orient="split", double_precision=5)
        logging.info("Summary statistics extracted.")
        logging.info("summary_json=%s", summary_json)
        
        # Add model metrics
        response = {
            "status": "completed",
            "summary": summary_json,
            # "model_info": {
            #     "num_observations": len(df),
            #     "channels": channel_columns,
            #     "adstock_max_lag": adstock_max_lag,
            #     "yearly_seasonality": yearly_seasonality
            # }
        }

        logging.info("run_mmm_task completed successfully.")
        logging.debug("response=%s", response)

        return response
    
    except Exception as e:
        logging.error("run_mmm_task failed: %s\nJSON data: %s", str(e), data, exc_info=True)
        return {"status": "failed", "error": str(e)} 


@app.route('/run_mmm_async', methods=['POST'])
def run_mmm_async():
    try:
        logging.info("Received request to run_mmm_async")
        data = request.get_json()
        logging.debug("run_mmm_async request data: %s", data)

        task = run_mmm_task.apply_async(args=[data])
        logging.info("Task submitted with ID: %s", task.id)

        # session[task.id] = "STARTED"

        return jsonify({"task_id": task.id})
    except Exception as e:
        logging.error("Error in run_mmm_async: %s", str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/get_results', methods=['GET'])
def get_results():
    try:
        task_id = request.args.get('task_id')
        logging.info("Received request for get_results with task_id: %s", task_id)

        # if task_id not in session:
        #     return jsonify({'status': "failure", "error":'No such task'}), 404

        task = run_mmm_task.AsyncResult(task_id)
        if task.state == 'PENDING':
            logging.info("Task %s is still pending.", task_id)
            response = {"status": "pending"}
        elif task.state != 'FAILURE':
            logging.info("Task %s completed successfully.", task_id)
            response = task.result
        else:
            logging.error("Task %s failed.", task_id)
            response = {"status": "failure", "error": str(task.info)}
        
        return jsonify(response)
    except Exception as e:
        logging.error("Error in get_results: %s", str(e), exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--port', default=5001, type=int)
    args = parser.parse_args()
    
    # Update this line to use args.port instead of hardcoded 8080
    app.run(host='0.0.0.0', port=args.port, debug=False)