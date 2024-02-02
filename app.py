from flask import Flask, request, jsonify
import pymc as pm
import arviz as az
from pymc_marketing.mmm import DelayedSaturatedMMM
import pandas as pd
import numpy as np
import json
import logging
import io
import os

from celery import Celery

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['broker_url'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['broker_url'])
celery.conf.update(app.config)
celery.conf.update(
    worker_concurrency=1,  # Number of process workers
    worker_pool='prefork',  # Use prefork (multiprocessing)
    task_always_eager=False  # Ensure tasks are not run locally by the worker that started them
)


@celery.task(bind=True)
def run_mmm_task(self, data):
    try:
        df = pd.read_json(io.StringIO(data["df"]), orient="split")

        # Extract optional parameters from 'data'
        date_column = data.get('date_column', 'date')
        channel_columns = data.get('channel_columns', [])
        adstock_max_lag = data.get('adstock_max_lag', 8)
        yearly_seasonality = data.get('yearly_seasonality', 2)

        # Define and fit the MMM model
        mmm = DelayedSaturatedMMM(
            date_column=date_column,
            channel_columns=channel_columns,
            adstock_max_lag=adstock_max_lag,
            yearly_seasonality=yearly_seasonality,
        )
        X = df.drop('sales', axis=1)
        y = df['sales']
        mmm.fit(X, y, chains=1, cores=1)

        # Extract and return summary statistics
        summary = az.summary(mmm.fit_result)
        summary_json = summary.to_json(orient='split')

        return {"status": "completed", "summary": summary_json}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@app.route('/run_mmm_async', methods=['POST'])
def run_mmm_async():
    task = run_mmm_task.apply_async(args=[request.get_json()])
    return jsonify({"task_id": task.id})

@app.route('/get_results', methods=['GET'])
def get_results():
    task_id = request.args.get('task_id')
    task = run_mmm_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {"status": "pending"}
    elif task.state != 'FAILURE':
        response = task.result
    else:
        response = {"status": "failure", "error": str(task.info)}
    return jsonify(response)



@app.route('/run_dynamic_pymc_model', methods=['POST'])
def run_dynamic_pymc_model():
    # Log the raw request data for debugging
    logging.debug("Received request data: %s", request.data)

    # Extract model code and data from the request
    model_code = request.json.get('model_code')
    data_dict = request.json.get('data_dict')
    # data_dict = {"x": np.array([1., 2., 3.]), "y": np.array([0.5, -1., 2.])}
    # Log extracted model code and data for debugging
    logging.debug("Model code: %s", model_code)
    logging.debug("Data: %s", data_dict)

    # Validate the model code and data
    # IMPORTANT: Ensure the model_code and data do not contain malicious elements

    # Execute the model with data
    results = eval_model_code(model_code, data_dict)

    # Log results for debugging
    logging.debug("Model results: %s", results)

    return jsonify(results)

def eval_model_code(model_code, data_dict):
    # Dynamically execute the model code with data
    try:
        # Make data_dict available in the local scope for the exec function
        local_scope = {'pm': pm, 'np': np, 'data_dict': data_dict}
        with pm.Model() as model:
            exec(model_code, globals(), local_scope)
            idata = pm.sample(draws=100, chains=1, cores=1)
            summary = pm.summary(idata)
        # Log summary for debugging
        logging.debug("Summary: %s", summary)
        return {'summary': str(summary)}
    except Exception as e:
        logging.error("Error in eval_model_code: %s", e)
        return {'error': str(e)}

@app.route('/debug', methods=['POST'])
def debug():
    # Log the raw request data for debugging
    logging.debug("Received request data: %s", request.data)

    # Extract model code and data from the request
    a = request.json.get('a')
    b = request.json.get('b')
    c = request.json.get('c')
    logging.debug(f"{a=}\n{b=}\n{c=}")

    return jsonify({"a": a, "b": b, "c": c})


@app.route('/run_mmm', methods=['POST'])
def run_mmm():
    try:
        data = request.get_json()
        df = pd.read_json(io.StringIO(data["df"]), orient="split")

        # Optional parameters with default values
        date_column = data.get('date_column', 'date')
        channel_columns = data.get('channel_columns', [])
        adstock_max_lag = data.get('adstock_max_lag', 8)
        yearly_seasonality = data.get('yearly_seasonality', 2)

        # Define the MMM model with optional parameters
        mmm = DelayedSaturatedMMM(
            date_column=date_column,
            channel_columns=channel_columns,
            adstock_max_lag=adstock_max_lag,
            yearly_seasonality=yearly_seasonality,
        )

        # Fit the model
        X = df.drop('sales', axis=1)
        y = df['sales']
        mmm.fit(X, y, chains=1, cores=1, nuts_sampler="numpyro")

        # Extract summary statistics from the trace
        summary = az.summary(mmm.fit_result)
        summary_json = summary.to_json(orient='split')
    except Exception as e:
        return jsonify({"status": "Error", "summary": str(e)})

    return jsonify({'status': 'Model executed successfully', 'summary': summary_json})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)