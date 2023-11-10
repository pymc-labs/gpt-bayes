import requests
import json

def test_api_response():
    model_code = """
    slope = pm.Normal('slope', mu=0, sigma=10)
    intercept = pm.Normal('intercept', mu=0, sigma=10)
    sigma = pm.HalfNormal('sigma', sigma=1)

    # Likelihood (sampling distribution) of observations
    likelihood = pm.Normal('y', mu=slope * data["x"] + intercept, sigma=sigma, observed=data["y"])
    """
    
    # Data to be sent
    data = {
        "x": [1., 2., 3.],
        "y": [.1, -2, 0.5]
    }
    
    # Payload that includes both model_code and data
    payload = {
        "model_code": model_code,
        "data": data
    }

    # Replace with your API endpoint
    url = "https://pymc-gpt-ed9cd0abd029.herokuapp.com"

    # Make a POST request with JSON payload
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(response)
    # Assert the status code
    assert response.status_code == 200

    # Parse the response
    response_data = response.json()
    
    # Additional assertions can be made here depending on your API's response structure
    # Example assertion
    assert "expected_field" in response_data

test_api_response()