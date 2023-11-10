from flask import Flask, request, jsonify
import pymc as pm
import numpy as np
import json

app = Flask(__name__)

@app.route('/run_dynamic_pymc_model', methods=['POST'])
def run_dynamic_pymc_model():
    # Extract model code and data from the request
    model_code = request.json.get('model_code')
    data = request.json.get('data', [])

    # Convert data to NumPy array
    data_array = np.array(data)

    # Validate the model code and data
    # IMPORTANT: Ensure the model_code and data do not contain malicious elements

    # Execute the model with data
    results = eval_model_code(model_code, data_array)

    return jsonify(results)

def eval_model_code(model_code, data):
    # Dynamically execute the model code with data
    # WARNING: Ensure robust validation of model_code and data to prevent security risks.
    try:
        # Make data available in the local scope for the exec function
        local_scope = {'data': data}
        exec(model_code, globals(), local_scope)
        trace = pm.sample(1000, nuts_sampler="numpyro")
        return {'summary': str(pm.summary(trace))}
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    app.run(debug=True)
