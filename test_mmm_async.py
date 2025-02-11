import requests
import json
import time
import pandas as pd

import sys
import io

def create_payload():
    payload = {
        "domain": "dev-nextgen-mmm.pymc-labs.com",
        "method": "post",
        "path": "/run_mmm_async",
        "operation": "runMMMAsync",
        "operation_hash": "0c869884cb92378e2dfe2ae377cac236cbc2b9d0",
        "is_consequential": True,
        "openaiFileIdRefs": [
            {
                "name": "mmm_example.csv",
                "id": "file-1234567890",
                "mime_type": "text/csv",
                "download_link": "https://raw.githubusercontent.com/pymc-labs/pymc-marketing/refs/heads/main/data/mmm_example.csv"
            }
        ],
        "date_column": "date_week",
        "channel_columns": [
            "x1",
            "x2"
        ],
        "adstock_max_lag": 8,
        "yearly_seasonality": 2,
        "y_column": "y"
    }
    return payload


def test_async_mmm_run(base_url):
    # Payload that includes data
    payload = create_payload()

    # Replace with your API endpoint for async run
    run_url = f"{base_url}/run_mmm_async"

    # Make a POST request to initiate the model run
    headers = {'Content-Type': 'application/json'}
    response = requests.post(run_url, data=json.dumps(payload), headers=headers)
    
    print(response)
    # Assert the status code for initiation
    assert response.status_code == 200

    # Extract task_id
    task_id = response.json()["task_id"]
    print(f"Got task_id {task_id}")

    # Polling URL
    results_url = f"{base_url}/get_summary_statistics?task_id={task_id}"

    # Poll for results
    while True:
        result_response = requests.get(results_url)
        result_data = result_response.json()

        if result_data["status"] == "completed":
            # Handle completed task
            
            # Perform additional assertions here
            summary = pd.read_json(io.StringIO(result_data["summary"]),orient='split')
            print('--------------------------------')
            print(summary)
            print('--------------------------------')
            print("Task completed:!!!")
            break
        elif result_data["status"] == "failed":
            # Handle failed task
            print("Task failed:", result_data)
            break
        elif result_data["status"] == "pending":
            # Wait before polling again
            print("Pending...")
            time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_script.py [local|deployed]")
        sys.exit(1)

    environment = sys.argv[1]
    
    if environment == "local":
        base_url = "http://localhost:5001"
    elif environment == "deployed-production":
        base_url = "https://nextgen-mmm.pymc-labs.com"
    elif environment == "deployed-development":
        base_url = "https://dev-nextgen-mmm.pymc-labs.com"
    else:
        print("Invalid argument. Use 'local' or 'deployed-production' or 'deployed-development'.")
        sys.exit(1)

    test_async_mmm_run(base_url)
