# GPT-Bayes Webapp

A cloud-based Marketing Mix Modeling (MMM) solution deployed on Google Cloud Platform.

## Quick Deployment
```bash
./deploy.sh production # Deploy the latest version to production
./deploy.sh development # Deploy the latest version to development
```

## System Architecture

GPT-Bayes consists of two main components:

1. **MMM Agent Alpha** - A specialized GPT model with API integration
   - Interface: [MMM Agent Alpha](https://chatgpt.com/g/g-67927a520a9481919cc163eb51bf1a3d-mmm-agent-alpha-2-0)
   - Authentication: social@pymc-labs.com
   - Function: Provides user interface for MMM analysis

2. **Backend Service**
   - Production URL: https://nextgen-mmm.pymc-labs.com
   - Development URL: https://dev-nextgen-mmm.pymc-labs.com
   - Function: Handles model fitting and parameter management via API endpoints
   - Infrastructure: Hosted on Google Cloud Engine (GCE) under the `gpt-bayes` project

## Project Structure

### Core Services
- `app.py` - Main Flask application
- `test_mmm_async.py` - Local API testing utility

### Infrastructure Configuration
- `nginx/` - NGINX reverse proxy settings
- `dockerfile` - Container specifications
- `start.sh` - Container initialization
- `build.sh` - Build the container image
- `deploy.sh` - Deployment automation
- `environment.yml` - Development environment specifications
- `config.yaml` - Environment configuration settings

### AI Agent Settings
- `gpt-agent/gpt_prompt.md` - System instructions
- `gpt-agent/api_spec.json` - API specifications
- `gpt-agent/knowledge/` - Reference documentation
- `gpt-agent/privacy_policy.md` - Data handling guidelines

### Testing Resources
- `test-data/` - Example datasets

## Deployment Guide

The application runs on Google Compute Engine (GCE) under the `gpt-bayes` project, accessible at `https://nextgen-mmm.pymc-labs.com` (production) and `https://dev-nextgen-mmm.pymc-labs.com` (development).

### Build and Push Docker Image

Build and push the Docker image to Google Artifact Registry (GAR).
```bash
./build.sh production # Build and publish to production
./build.sh development # Build and publish to development
```

### Standard Deployment

Once the Docker image is built and pushed to GAR, use `deploy.sh` to update the application. This script handles:
- Updating the container in Google Artifact Registry (GAR)
- Deploying to the specified environment

```bash
./deploy.sh production # Deploy the latest version to production
./deploy.sh development # Deploy the latest version to development
```

### Server Management

Access the specified server:
```bash
gcloud compute ssh gpt-bayes --zone us-central1-a
gcloud compute ssh dev-gpt-bayes --zone us-central1-a
```

Container management commands:
```bash
# List containers
docker ps -a

# Monitor container logs
docker attach CONTAINER_ID

# Access container shell
docker exec -it CONTAINER_ID /bin/bash
```


### Container Registry Management

Build and publish to Google Artifact Registry:
```bash
./build.sh production # Build and publish to production
./build.sh development # Build and publish to development
```

Note: This updates the container image but doesn't affect the specified deployment.

### Server Instance Management

View available Container-Optimized OS images:
```bash
gcloud compute images list --project cos-cloud --no-standard-images
```

Update specified container:
```bash
# Clear existing containers
gcloud compute ssh gpt-bayes --zone us-central1-a --command 'docker system prune -f -a'
gcloud compute ssh dev-gpt-bayes --zone us-central1-a --command 'docker system prune -f -a'

# Deploy new container
gcloud compute instances update-container gpt-bayes \
  --zone=us-central1-a \
  --container-image=us-central1-docker.pkg.dev/bayes-gpt/gpt-bayes/gpt-bayes:latest

gcloud compute instances update-container dev-gpt-bayes \
  --zone=us-central1-a \
  --container-image=us-central1-docker.pkg.dev/bayes-gpt/dev-gpt-bayes/dev-gpt-bayes:latest
```

Create new server instance:
```bash
 gcloud compute instances create-with-container gpt-bayes \
  --machine-type e2-standard-4 \
  --boot-disk-size 20GB \
  --image cos-stable-117-18613-164-4 \
  --image-project cos-cloud \
  --zone us-central1-a \
  --container-image=us-central1-docker.pkg.dev/bayes-gpt/gpt-bayes/gpt-bayes:latest \
  --tags http-server,https-server,allow-tcp-5000

 gcloud compute instances create-with-container dev-gpt-bayes \
  --machine-type e2-standard-4 \
  --boot-disk-size 20GB \
  --image cos-stable-117-18613-164-4 \
  --image-project cos-cloud \
  --zone us-central1-a \
  --container-image=us-central1-docker.pkg.dev/bayes-gpt/dev-gpt-bayes/dev-gpt-bayes:latest \
  --tags http-server,https-server,allow-tcp-5000

```

### NGINX Configuration (Advanced)

Deploy NGINX reverse proxy updates:
```bash
cd nginx
./deploy.sh production # Deploy the latest version to production
./deploy.sh development # Deploy the latest version to development
```

Update backend IP address:
1. Navigate to `config.yaml`
2. Modify the `ipAddress` directive with the new IP
3. Example: `ipAddress: 35.208.203.115`

## Local Development

### 1. Environment Setup

Create development environment:
```bash
# Using conda
conda env create -f environment.yml

# Using mamba (faster)
mamba env create -f environment.yml

# Activate environment
conda activate base
```

### 2. Development Server

Launch the development stack:

1. Start Redis:
```bash
redis-server
```

2. Start Celery worker (new terminal):
```bash
celery -A app.celery worker --loglevel=info
```

3. Start Flask (new terminal):
```bash
python app.py --port 5001
```

4. Run tests:
```bash
# Test local instance
python test_mmm_async.py local

# Test production instance
python test_mmm_async.py deployed
```

The test suite:
- Generates sample MMM data
- Submits to specified API endpoint
- Monitors result generation
- Displays model analytics
