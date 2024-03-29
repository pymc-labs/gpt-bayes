from flask import Flask, request, jsonify
import pymc as pm
import arviz as az
from pymc_marketing.mmm import DelayedSaturatedMMM
import pandas as pd
import numpy as np
import json
import logging
from google.cloud import logging as google_logging
import io
import os
from celery import Celery

__version__ = "0.3"

running_in_google_cloud = os.environ.get('RUNNING_IN_GOOGLE_CLOUD', 'False').lower() == 'true'

# Configure standard logging
logging.basicConfig(level=logging.DEBUG)
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

app = Flask(__name__)
app.config['broker_url'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['broker_url'])
celery.conf.update(app.config)
celery.conf.update(
    worker_pool='prefork',  # Use prefork (multiprocessing)
    task_always_eager=False  # Ensure tasks are not run locally by the worker that started them
)

logging.info(f"App started. Version: {__version__}")

@celery.task(bind=True)
def run_mmm_task(self, data):
    try:
        logging.info("Starting run_mmm_task")

        df = pd.read_json(io.StringIO(data["df"]), orient="split")
        logging.debug(f"DataFrame loaded with {len(df)} rows.")

        # Extract optional parameters from 'data'
        date_column = data.get('date_column', 'date')
        channel_columns = data.get('channel_columns', [])
        adstock_max_lag = data.get('adstock_max_lag', 8)
        yearly_seasonality = data.get('yearly_seasonality', 2)
        logging.debug(f"Parameters extracted: date_column={date_column}, channel_columns={channel_columns}, adstock_max_lag={adstock_max_lag}, yearly_seasonality={yearly_seasonality}")

        # Define and fit the MMM model
        mmm = DelayedSaturatedMMM(
            date_column=date_column,
            channel_columns=channel_columns,
            adstock_max_lag=adstock_max_lag,
            yearly_seasonality=yearly_seasonality,
        )
        logging.info("MMM model defined.")

        X = df.drop('sales', axis=1)
        y = df['sales']
        logging.debug("Starting model fitting.")
        mmm.fit(X, y, chains=1, cores=1)
        logging.info("Model fitting completed.")

        # Extract and return summary statistics
        summary = az.summary(mmm.fit_result, 
                             var_names=[
                                "intercept",
                                "likelihood_sigma",
                                "beta_channel",
                                "alpha",
                                "lam",],
                            kind="stats")
        summary_json = summary.to_json(orient="split")
        logging.info("Summary statistics extracted.")

        logging.info("run_mmm_task completed successfully.")
        logging.debug(f"summary_json={summary_json}")
        return {"status": "completed", "summary": summary_json}
    except Exception as e:
        logging.error(f"run_mmm_task failed: {str(e)}\nJSON data: {data}", exc_info=True)
        return {"status": "failed", "error": str(e)}

@app.route('/run_mmm_async', methods=['POST'])
def run_mmm_async():
    try:
        logging.info("Received request to run_mmm_async")
        data = request.get_json()
        logging.debug(f"run_mmm_async request data: {data}")

        task = run_mmm_task.apply_async(args=[data])
        logging.info(f"Task submitted with ID: {task.id}")

        # session[task.id] = "STARTED"

        return jsonify({"task_id": task.id})
    except Exception as e:
        logging.error(f"Error in run_mmm_async: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/get_results', methods=['GET'])
def get_results():
    try:
        task_id = request.args.get('task_id')
        logging.info(f"Received request for get_results with task_id: {task_id}")

        # if task_id not in session:
        #     return jsonify({'status': "failure", "error":'No such task'}), 404

        task = run_mmm_task.AsyncResult(task_id)
        if task.state == 'PENDING':
            logging.info(f"Task {task_id} is still pending.")
            response = {"status": "pending"}
        elif task.state != 'FAILURE':
            logging.info(f"Task {task_id} completed successfully.")
            response = task.result
        else:
            logging.error(f"Task {task_id} failed.")
            response = {"status": "failure", "error": str(task.info)}
        
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error in get_results: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)