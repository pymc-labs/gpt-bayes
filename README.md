# Deploying Your Application with Google Cloud Build

This repository provides the necessary configurations for deploying your application using Google Cloud Build.

## Deploy NGINX Reverse Proxy

To deploy the NGINX Reverse Proxy, navigate to the `nginx` directory and execute the following commands:

```bash
cd nginx
gcloud builds submit
```

This process will build a Docker container, push it to Google Artifact Registry (GAR), and deploy it to Cloud Run.

## Modify IP in NGINX Reverse Proxy

To update the IP address in the NGINX Reverse Proxy configuration, navigate to the `nginx` directory, edit the `nginx.conf` file, and modify the value of the IP in the `proxy_pass` directive:

```bash
cd nginx
# Open nginx.conf in your preferred text editor and update the IP
# Example: proxy_pass http://35.208.203.115:5000;
```

## Build and Push Webapp Container to Google Artifact Registry (GAR)

Execute the following command to build and push the web application container to Google Artifact Registry:

```bash
gcloud builds submit
```

This process will build a Docker container, push it to Google Artifact Registry (GAR).
This doesn't deploy to Google Compute Engine (GCE).

## Deploy to Google Compute Engine (GCE)

List Container-Optimized OS (COS) image names:

```bash
gcloud compute images list --project cos-cloud --no-standard-images
```

Update container:
```bash
gcloud compute ssh gpt-bayes --zone us-central1-a --command 'docker system prune -f -a'

gcloud compute instances update-container gpt-bayes \
  --zone=us-central1-a \
  --container-image=us-central1-docker.pkg.dev/bayes-gpt/gpt-bayes/gpt-bayes:latest
```

Deploy:

```bash
gcloud compute instances create gpt-bayes \
 --machine-type e2-standard-4 \
 --boot-disk-size 20GB \
 --image image-name \
 --image-project cos-cloud \
 --zone us-central1 \
 --metadata container-image=your-container-image-name \
 --tags http-server \
 --firewall-create allow-http
```

# Local Development Setup

### 1. Create Conda Environment

First, create a conda environment using the provided `environment.yml` file:

```bash
conda env create -f environment.yml
```

Or if you prefer using mamba (faster alternative):

```bash
mamba env create -f environment.yml
```

Activate the environment:
```bash
conda activate base
```

### 2. Local Testing Setup

To test the application locally, follow these steps:

1. Start the Redis server (installed via conda):
```bash
redis-server
```

2. Start the Celery worker (in a new terminal):
```bash
celery -A app.celery worker --loglevel=info
```

3. Start the Flask application (in another terminal):
```bash
python app.py --port 5001
```

4. Run the test suite:
```bash
python test_mmm_async.py local
```

The test will:
- Generate sample marketing mix modeling data
- Submit it to the local API endpoint
- Poll for results until completion
- Display the model summary statistics

Note: The test script accepts either `local` or `deployed` as an argument to switch between testing the local instance (`http://localhost:5001`) or the deployed version.

### 3. Troubleshooting

Common issues and solutions:
- If Redis fails to start, ensure no other Redis instance is running: `sudo service redis-server stop`
- If the Celery worker fails to connect, verify Redis is running on port 6379
- If the test script fails, ensure all three components (Redis, Celery, Flask) are running
- For port conflicts, you can modify the Flask port (default: 5001) in the app.py startup command



