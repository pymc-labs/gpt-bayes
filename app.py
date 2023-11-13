from flask import Flask, request, jsonify
import pymc as pm
import numpy as np
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

@app.route('/run_dynamic_pymc_model', methods=['POST'])
def run_dynamic_pymc_model():
    # Log the raw request data for debugging
    logging.debug("Received request data: %s", request.data)

    # Extract model code and data from the request
    model_code = request.json.get('model_code')
    data_dict = request.json.get('data', {})

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
        local_scope = {'pm': pm, 'np': np, 'data': data_dict}
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

if __name__ == '__main__':
    app.run() #threaded=False, workers=4)
