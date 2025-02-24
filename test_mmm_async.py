import requests
import json
import time
import pandas as pd
import os
import sys
import io
import dotenv

dotenv.load_dotenv()

API_KEY = os.environ.get('API_KEY', None)

def create_payload(include_file_refs=True):
    openaiFileIdRefs = []
    if include_file_refs:
        openaiFileIdRefs = [
            {
                "name": "mmm_example.csv",
                "id": "file-1234567890",
                "mime_type": "text/csv",
                "download_link": "https://raw.githubusercontent.com/pymc-labs/pymc-marketing/refs/heads/main/data/mmm_example.csv"
            }
        ]
    payload = {
        "domain": "dev-nextgen-mmm.pymc-labs.com",
        "method": "post",
        "path": "/run_mmm_async",
        "operation": "runMMMAsync",
        "operation_hash": "0c869884cb92378e2dfe2ae377cac236cbc2b9d0",
        "is_consequential": True,
        "openaiFileIdRefs": openaiFileIdRefs,
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

def test_missing_file_refs(base_url):
    payload = create_payload(include_file_refs=False)
    run_url = f"{base_url}/run_mmm_async"
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    response = requests.post(run_url, data=json.dumps(payload), headers=headers)
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid request format"

def test_async_mmm_run(base_url):
    # Payload that includes data
    payload = create_payload()

    # Replace with your API endpoint for async run
    run_url = f"{base_url}/run_mmm_async"

    # Make a POST request to initiate the model run
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    response = requests.post(run_url, data=json.dumps(payload), headers=headers)
    
    # Assert the status code for initiation
    assert response.status_code == 200

    # Extract task_id
    task_id = response.json()["task_id"]
    print(f"Got task_id {task_id}")

    # Polling URL
    results_url = f"{base_url}/get_summary_statistics?task_id={task_id}"

    # Poll for results
    while True:
        result_response = requests.get(results_url, headers=headers)
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

def test_load(base_url, num_concurrent_runs):
    """
    Test the server under load with multiple concurrent model fits.
    
    Args:
        base_url: The base URL of the API
        num_concurrent_runs: Number of concurrent model fits to run
    """
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY
    }
    
    # Start all runs and collect task IDs
    task_ids = []
    start_time = time.time()
    
    print(f"\nStarting {num_concurrent_runs} concurrent model fits...")
    
    for i in range(num_concurrent_runs):
        payload = create_payload()
        run_url = f"{base_url}/run_mmm_async"
        response = requests.post(run_url, data=json.dumps(payload), headers=headers)
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        task_ids.append(task_id)
        print(f"Started task {i+1}/{num_concurrent_runs}: {task_id}")
    
    # Monitor all tasks until completion
    completed_tasks = 0
    while completed_tasks < num_concurrent_runs:
        for task_id in task_ids:
            results_url = f"{base_url}/get_summary_statistics?task_id={task_id}"
            result_response = requests.get(results_url, headers=headers)
            result_data = result_response.json()
            
            if result_data["status"] == "completed" and task_id in task_ids:
                task_ids.remove(task_id)
                completed_tasks += 1
                print(f"Task {task_id} completed. {completed_tasks}/{num_concurrent_runs} done.")
            elif result_data["status"] == "failed" and task_id in task_ids:
                task_ids.remove(task_id)
                completed_tasks += 1
                print(f"Task {task_id} failed!")
                
        if task_ids:  # If there are still pending tasks
            time.sleep(10)
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nAll {num_concurrent_runs} tasks completed in {total_time:.2f} seconds")
    print(f"Average time per task: {total_time/num_concurrent_runs:.2f} seconds")
    return total_time

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

    test_missing_file_refs(base_url)
    test_async_mmm_run(base_url)

    # After existing tests, run load tests
    print("\n=== Running Load Tests ===")
    
    loads = [1, 5, 10, 25]
    results = {}
    
    for load in loads:
        print(f"\nTesting with {load} concurrent runs...")
        total_time = test_load(base_url, load)
        results[load] = total_time
    
    print("\n=== Load Test Summary ===")
    print("Concurrent Runs | Total Time (s) | Avg Time per Run (s)")
    print("----------------|----------------|-------------------")
    for load, time in results.items():
        print(f"{load:14d} | {time:14.2f} | {time/load:19.2f}")
