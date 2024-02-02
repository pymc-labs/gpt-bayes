import requests
import json
import time
import pandas as pd
import numpy as np

def create_payload():
    # Number of weeks
    n_weeks = 52

    # Generate weekly dates
    dates = pd.date_range(start='2023-01-01', periods=n_weeks, freq='W')

    # Generate synthetic sales data (random for example purposes)
    sales = np.random.randint(1000, 5000, size=n_weeks)

    # Generate synthetic marketing spend data
    tv_spend = np.random.randint(1000, 3000, size=n_weeks)
    online_spend = np.random.randint(500, 2000, size=n_weeks)

    # Create DataFrame
    data = pd.DataFrame({
        'date': dates,
        'sales': sales,
        'tv': tv_spend,
        'online': online_spend
    })

    # Convert DataFrame to JSON for payload
    data_json = data.to_json(orient='split')

    # Example payload
    payload = {
        "df": data_json,
        "date_column": "date",
        "channel_columns": ["tv", "online"],
        "adstock_max_lag": 8,
        "yearly_seasonality": 2
    }

    return payload

def test_async_mmm_run():
    # Payload that includes data
    payload = create_payload()

    # Replace with your API endpoint for async run
    run_url = "http://localhost:5001/run_mmm_async"

    # Make a POST request to initiate the model run
    headers = {'Content-Type': 'application/json'}
    response = requests.post(run_url, data=json.dumps(payload), headers=headers)
    
    # Assert the status code for initiation
    assert response.status_code == 200

    # Extract task_id
    task_id = response.json()["task_id"]

    # Polling URL
    results_url = f"http://localhost:5001/get_results?task_id={task_id}"

    # Poll for results
    while True:
        result_response = requests.get(results_url)
        result_data = result_response.json()

        if result_data["status"] == "completed":
            # Handle completed task
            print("Task completed:", result_data)
            # Perform additional assertions here
            break
        elif result_data["status"] == "failed":
            # Handle failed task
            print("Task failed:", result_data)
            break
        elif result_data["status"] == "pending":
            # Wait before polling again
            time.sleep(2)

test_async_mmm_run()
