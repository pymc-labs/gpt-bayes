import requests
import json
import pandas as pd
import os
import io
import dotenv
import time
import sys
dotenv.load_dotenv()

def create_test_payload():
    """Create test payload with example data"""
    return {
        "openaiFileIdRefs": [{
            "name": "mmm_example.csv",
            "id": "file-1234567890", 
            "mime_type": "text/csv",
            "download_link": "https://raw.githubusercontent.com/pymc-labs/pymc-marketing/refs/heads/main/data/mmm_example.csv"
        }],
        "date_column": "date_week",
        "channel_columns": ["x1", "x2"],
        "adstock_max_lag": 8,
        "yearly_seasonality": 2,
        "y_column": "y"
    }

def test_cloudrun_mmm():
    """Test the Cloud Run MMM endpoint"""
    
    # Get Cloud Run URL from environment
    cloud_run_url = os.environ.get("CLOUD_RUN_URL")
    if not cloud_run_url:
        raise ValueError("CLOUD_RUN_URL environment variable not set")

    # Create headers with auth token
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.popen("gcloud auth print-identity-token").read().strip()}'
    }

    # Test missing payload
    # print("\nTesting missing payload...")
    # response = requests.post(f"{cloud_run_url}/run_mmm", headers=headers)
    # assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
    # assert "No JSON payload provided" in response.json()["error"]

    # Test missing file refs
    # print("\nTesting missing file refs...")
    # response = requests.post(
    #     f"{cloud_run_url}/run_mmm",
    #     headers=headers,
    #     json={"date_column": "date"}
    # )
    # assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
    # assert "No file references provided" in response.json()["error"]

    # Test full MMM run
    print("\nTesting full MMM run...")
    payload = create_test_payload()
    
    start_time = time.time()
    response = requests.post(
        f"{cloud_run_url}/run_mmm", 
        headers=headers,
        json=payload
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "completed"
    assert "model_filename" in result
    assert "summary" in result
    
    # Print summary statistics
    summary = pd.read_json(io.StringIO(json.dumps(result["summary"])))
    print("\nModel Summary:")
    print(summary)
    
    end_time = time.time()
    print(f"\nTotal execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_script.py [local|deployed]")
        sys.exit(1)

    environment = sys.argv[1]
    
    if environment == "local":
        base_url = "http://localhost:8080"
    elif environment == "production":
        base_url = "https://nextgen-mmm.pymc-labs.com"
    elif environment == "development":
        CLOUD_RUN_URL = "https://dev-gpt-bayes-cloudrun-i66d5bzhua-uc.a.run.app"
    else:
        print("Invalid argument. Use 'local' or 'production' or 'development'.")
        sys.exit(1)

    test_cloudrun_mmm()
