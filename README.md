# GPT-Bayes

A cloud-based service that combines GPT models with Bayesian inference for advanced marketing mix modeling (MMM) analysis.

## Overview

GPT-Bayes is a demo that leverages the power of large language models and Bayesian statistics to provide intelligent marketing mix modeling solutions. The platform is built with a microservices architecture, deployed on Google Cloud Platform, and features both development and production environments.

## Project Structure

```
.
├── server/             # Main backend server implementation
├── gpt-agent/         # GPT integration and prompt engineering
├── cloudrun/          # Google Cloud Run service configurations
├── nginx/             # Nginx proxy configurations
├── test-data/         # Test datasets and fixtures
└── config.yaml        # Environment and deployment configurations
```

## Key Components

### Backend Server (server/)

The backend server is built with Python and includes:
- Flask-based REST API
- Celery for asynchronous task processing
- Containerized deployment using Docker
- Comprehensive API documentation (OpenAPI)
- Environment management with Conda

Key files:
- `app.py`: Main application entry point
- `routes.py`: API endpoint definitions
- `config_server.py`: Server configuration
- `celery_setup.py`: Async task queue setup
- `utils.py`: Utility functions
- `test_mmm_async.py`: Asynchronous MMM testing

### Cloud Run Service (cloudrun/)

The Cloud Run service is a serverless component responsible for running the Marketing Mix Models (MMM) in a scalable environment. It provides:

- **Model Training Endpoint**: REST API endpoint for training MMM models
- **Cloud Storage Integration**: Automatic model persistence to GCP buckets
- **Scalable Infrastructure**: Serverless deployment that scales based on demand

Key components:
- `app.py`: Flask application with MMM training endpoint
  - Handles CSV data ingestion
  - Configures and trains PyMC Marketing models
  - Serializes and stores models in Cloud Storage
  - Returns model summaries using ArviZ
- `Dockerfile`: Container configuration for the service
- `requirements.txt`: Python dependencies including:
  - Flask for the web server
  - PyMC Marketing for Bayesian MMM
  - NumPyro for MCMC sampling
  - ArviZ for statistical analysis
  - Google Cloud Storage for model persistence

Deployment scripts:
- `build.sh`: Container image building
- `deploy.sh`: Cloud Run deployment automation
- `cloudrun.yaml`: Service configuration

The service accepts POST requests with:
- CSV data URL
- Model configuration parameters
  - Date column specification
  - Channel columns for marketing activities
  - Adstock parameters
  - Seasonality settings

Returns:
- Trained model filename in Cloud Storage
- Model summary statistics
- Training status and any error messages

### GPT Integration (gpt-agent/)

Contains the GPT model integration components:
- Custom prompt engineering
- Knowledge base for domain-specific information
- Privacy policy and data handling guidelines

### Infrastructure

- **Cloud Run Service**: Scalable, containerized deployment
- **Nginx Proxy**: Reverse proxy and load balancing
- **Google Cloud Platform**: Cloud infrastructure and services

## Configuration

The project uses a `config.yaml` file for environment-specific settings:

### Production
- Region: us-central1
- Custom domain: nextgen-mmm.pymc-labs.com
- Dedicated model storage bucket

### Development
- Separate development environment
- Development-specific endpoints and resources
- Isolated model storage

## Deployment

Deployment is managed through shell scripts and Cloud Build:

1. `server/build.sh`: Builds the Docker container
2. `server/deploy.sh`: Handles deployment to GCP
3. `cloudbuild.yaml`: CI/CD pipeline configuration

## Environment Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   cd server
   conda env create -f environment.yml
   ```
3. Set up environment variables:
   ```bash
   cp server/.env.example server/.env
   # Configure your environment variables
   ```

## Development

1. Activate the conda environment:
   ```bash
   conda activate <environment_name>
   ```
2. Start the development server:
   ```bash
   cd server
   ./start.sh
   ```

## Testing

Run the test suite:
```bash
cd server
python -m pytest test_mmm_async.py
```

## API Documentation

The API specification is available in `server/api_spec.json`. When the server is running, visit `/docs` for the interactive Swagger documentation.

## Security

- All endpoints are protected with appropriate authentication
- Sensitive data is handled according to the privacy policy
- Environment-specific configurations ensure isolation between development and production
