# GPT-Bayes Webapp

A cloud-based Marketing Mix Modeling (MMM) solution deployed on Google Cloud Platform.

## Quick Deployment
```bash
./deploy.sh  # Deploy the latest version to production
```

## System Architecture

GPT-Bayes consists of two main components:

1. **MMM Agent Alpha** - A specialized GPT model with API integration
   - Interface: [MMM Agent Alpha](https://chatgpt.com/g/g-67927a520a9481919cc163eb51bf1a3d-mmm-agent-alpha-2-0)
   - Authentication: social@pymc-labs.com
   - Function: Provides user interface for MMM analysis

2. **Backend Service**
   - Production URL: https://nextgen-mmm.pymc-labs.com
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
- `deploy.sh` - Deployment automation
- `environment.yml` - Development environment specifications

### AI Agent Settings
- `gpt-agent/gpt_prompt.md` - System instructions
- `gpt-agent/api_spec.json` - API specifications
- `gpt-agent/knowledge/` - Reference documentation
- `gpt-agent/privacy_policy.md` - Data handling guidelines

### Testing Resources
- `test-data/` - Example datasets

## Deployment Guide

The application runs on Google Compute Engine (GCE) under the `gpt-bayes` project, accessible at `https://nextgen-mmm.pymc-labs.com`.

### Standard Deployment

Use `deploy.sh` to update the application. This script handles:
- Updating the container in Google Artifact Registry (GAR)
- Deploying to the production environment

```bash
./deploy.sh
```

### Server Management

Access the production server:
```bash
gcloud compute ssh gpt-bayes --zone us-central1-a
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
gcloud builds submit
```

Note: This updates the container image but doesn't affect the production deployment.

### Server Instance Management

View available Container-Optimized OS images:
```bash
gcloud compute images list --project cos-cloud --no-standard-images
```

Update production container:
```bash
# Clear existing containers
gcloud compute ssh gpt-bayes --zone us-central1-a --command 'docker system prune -f -a'

# Deploy new container
gcloud compute instances update-container gpt-bayes \
  --zone=us-central1-a \
  --container-image=us-central1-docker.pkg.dev/bayes-gpt/gpt-bayes/gpt-bayes:latest
```

Create new server instance:
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

### NGINX Configuration (Advanced)

Deploy NGINX reverse proxy updates:
```bash
cd nginx
gcloud builds submit
```

Update backend IP address:
1. Navigate to `nginx/nginx.conf`
2. Modify the `proxy_pass` directive with the new IP
3. Example: `proxy_pass http://35.208.203.115:5000;`

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
