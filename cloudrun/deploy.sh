#!/bin/bash

# Validate environment argument
if [ "$1" != "production" ] && [ "$1" != "development" ]; then
    echo "Error: Environment must be specified as either 'production' or 'development'"
    echo "Usage: $0 <environment>"
    exit 1
fi

ENVIRONMENT=$1

# Function to read config value
get_config() {
    local key=$1
    yq ".$ENVIRONMENT.$key" ../config.yaml | tr -d '"'
}

# Function to read config value
get_cloudrun_config() {
    local key=$1
    yq ".$ENVIRONMENT.cloudRun.$key" ../config.yaml | tr -d '"'
}

# Get configuration values
INSTANCE_NAME=$(get_config "instanceName")
REGION=$(get_config "region")
ZONE=$(get_config "zone")
CLOUD_RUN_SERVICE_NAME=$(get_cloudrun_config "serviceName")
CLOUD_RUN_MODEL_BUCKET=$(get_cloudrun_config "modelBucket")

# Updated command syntax for Cloud Run deployment
gcloud run deploy "$CLOUD_RUN_SERVICE_NAME" \
  --image "$REGION-docker.pkg.dev/bayes-gpt/$INSTANCE_NAME/$CLOUD_RUN_SERVICE_NAME:latest" \
  --platform managed \
  --region "$REGION" \
  --set-env-vars MODEL_BUCKET=$CLOUD_RUN_MODEL_BUCKET \
  --no-allow-unauthenticated