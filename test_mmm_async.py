import requests
import json
import time
import pandas as pd

import sys
import io

def create_payload_csv():
    # Load the user-uploaded data file
    data = pd.read_csv('test-data/mmm_example.csv')
    # Rename the 'y' column to 'sales' and select relevant columns
    data.rename(columns={'y': 'sales'}, inplace=True)
    mmm_data = data[['date_week', 'sales', 'x1', 'x2', 'event_1', 'event_2', 't']]

    # Convert 'date_week' to datetime format
    mmm_data.loc[:, 'date_week'] = pd.to_datetime(mmm_data['date_week']).dt.strftime('%Y-%m-%d')

    # Convert the prepared data to JSON format for payload, ensuring proper formatting
    data_json = mmm_data.to_json(orient="split", index=False)
    #print(data_json)
    # Example payload
    payload = {
        "df": data_json,
        "date_column": "date_week",
        "channel_columns": ["x1", "x2"],
        "adstock_max_lag": 2,
        "yearly_seasonality": 8,
        "control_columns": ["event_1", "event_2", "t"]
    }

    return payload


def test_async_mmm_run(base_url):
    # Payload that includes data
    payload = create_payload_csv()

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
    results_url = f"{base_url}/get_results?task_id={task_id}"

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
