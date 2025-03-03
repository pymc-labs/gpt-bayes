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
API_KEY=$(grep API_KEY .env | cut -d "'" -f 2)
INSTANCE_NAME=$(get_config "instanceName")
REGION=$(get_config "region")
CLOUD_RUN_MODEL_BUCKET=$(get_cloudrun_config "modelBucket")
CLOUD_RUN_URL=$(get_cloudrun_config "url")

echo "Building $INSTANCE_NAME in $REGION"

gcloud builds submit --config cloudbuild.yaml \
--project=bayes-gpt \
--substitutions=_REPO_NAME=$INSTANCE_NAME,\
_SERVICE_NAME=$INSTANCE_NAME,\
_REGION=$REGION,\
_API_KEY=$API_KEY,\
_MODEL_BUCKET=$CLOUD_RUN_MODEL_BUCKET,\
_CLOUD_RUN_URL=$CLOUD_RUN_URL
