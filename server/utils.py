import json
import os
from functools import wraps
from flask import request, jsonify
from config_server import API_KEY, CLOUD_RUN_URL
import logging

def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return func(*args, **kwargs)
        return jsonify({"message": "Incorrect or missing API key"}), 401
    return decorated_function

def get_mmm_request_schema():
    """Extract the request schema from the OpenAPI spec"""
    try:
        with open('api_spec.json', 'r') as f:
            api_spec = json.load(f)
            return api_spec['paths']['/run_mmm_async']['post']['requestBody']['content']['application/json']['schema']
    except Exception as e:
        logging.error("Failed to load API spec: %s", str(e))
        raise e

def get_cloud_run_auth_token():
    """Get authentication token for Cloud Run"""
    try:
        import google.auth.transport.requests
        import google.oauth2.id_token

        auth_req = google.auth.transport.requests.Request()
        id_token = google.oauth2.id_token.fetch_id_token(auth_req, CLOUD_RUN_URL)
        logging.info("Got Cloud Run ID token: %s", id_token)
        
        return id_token
    except Exception as e:
        logging.error("Failed to get Cloud Run auth token: %s", str(e))
        raise 