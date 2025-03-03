from flask import request, jsonify, send_file
from functools import wraps
from jsonschema import validate
import logging
import requests
import dill
from google.cloud import storage
import arviz as az
from utils import require_api_key, get_mmm_request_schema, get_cloud_run_auth_token
from config_server import API_KEY, CLOUD_RUN_URL, MODEL_BUCKET

def register_routes(app):
    celery = app.extensions["celery"]

    @celery.task(name="run_mmm_task")
    def run_mmm_task(data):
        try:
            # Get Cloud Run auth token and make request
            auth_token = get_cloud_run_auth_token()
            logging.info("Cloud Run auth token: %s", auth_token)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {auth_token}'
            }
            
            response = requests.post(
                f"{CLOUD_RUN_URL}/run_mmm",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error("Error in run_mmm_task: %s", str(e), exc_info=True)
            raise

    @app.route('/run_mmm_async', methods=['POST'])
    @require_api_key
    def run_mmm_async():
        try:
            logging.info("Received request to run_mmm_async")
            data = request.get_json()
            logging.debug("run_mmm_async request data: %s", data)

            # Validate request schema
            schema = get_mmm_request_schema()
            validate(instance=data, schema=schema)

            # Submit task to Celery
            task = run_mmm_task.delay(data)

            return jsonify({
                "status": "accepted",
                "task_id": task.id
            })

        except Exception as e:
            logging.error("Error in run_mmm_async: %s", str(e), exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route('/get_task_status', methods=['GET'])
    @require_api_key
    def get_task_status():
        try:
            task_id = request.args.get('task_id')
            if not task_id:
                return jsonify({"error": "No task_id provided"}), 400

            task = run_mmm_task.AsyncResult(task_id)
            
            if task.state == 'PENDING':
                response = {
                    'status': 'pending',
                    'task_id': task_id
                }
            elif task.state == 'SUCCESS':
                result = task.get()
                response = {
                    'status': 'completed',
                    'task_id': task_id,
                    'model_filename': result.get('model_filename'),
                    'summary': result.get('summary')
                }
            elif task.state == 'FAILURE':
                response = {
                    'status': 'failed',
                    'task_id': task_id,
                    'error': str(task.info)
                }
            else:
                response = {
                    'status': task.state.lower(),
                    'task_id': task_id
                }
            
            return jsonify(response)

        except Exception as e:
            logging.error("Error in get_task_status: %s", str(e), exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route('/get_summary_statistics', methods=['GET'])
    @require_api_key
    def get_summary_statistics():
        try:
            model_filename = request.args.get('model_filename')
            if not model_filename:
                return jsonify({"error": "No model_filename provided"}), 400

            # Download and process model
            storage_client = storage.Client()
            bucket = storage_client.bucket(MODEL_BUCKET)
            blob = bucket.blob(model_filename)
            
            model_bytes = blob.download_as_bytes()
            mmm = dill.loads(model_bytes)
            
            # Generate summary statistics
            summary = az.summary(mmm.fit_result)
            important_params = summary[summary.index.str.contains(
                'alpha|beta|sigma|intercept|lam|gamma_control', 
                case=False
            )].round(5)
            
            summary_json = important_params.to_json(orient="split", double_precision=5)
            logging.info("Summary statistics extracted.")

            return jsonify({"status": "completed", "summary": summary_json})
            
        except Exception as e:
            logging.error("Error in get_summary_statistics: %s", str(e), exc_info=True)
            return jsonify({"status": "failure", "error": str(e)}), 500 
        
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok"})
    
    # Route to serve OpenAPI JSON spec
    @app.route('/api_spec.json')
    def serve_openapi_json():
        return send_file("api_spec.json", mimetype="application/json")