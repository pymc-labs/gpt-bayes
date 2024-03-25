import requests
import json
import time
import pandas as pd
import numpy as np
import sys

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
    data_json = data.to_json(orient="split")

    # Example payload
    payload = {
        "df": data_json,
        "date_column": "date",
        "channel_columns": ["tv", "online"],
        "adstock_max_lag": 2,
        "yearly_seasonality": 2
    }

    return payload

def create_payload_csv():
    # Load the user-uploaded data file
    data = pd.read_csv('mmm_example.csv')
    # Rename the 'y' column to 'sales' and select relevant columns
    data.rename(columns={'y': 'sales'}, inplace=True)
    mmm_data = data[['date_week', 'sales', 'x1', 'x2']]

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
        "yearly_seasonality": 8
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
            print("Task completed:", result_data)
            # Perform additional assertions here
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
    elif environment == "deployed":
        base_url = "https://gcr2gce-proxy-i66d5bzhua-uc.a.run.app"
    else:
        print("Invalid argument. Use 'local' or 'deployed'.")
        sys.exit(1)

    test_async_mmm_run(base_url)
