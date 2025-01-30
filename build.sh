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
    yq ".$ENVIRONMENT.$key" config.yaml | tr -d '"'
}

# Get configuration values
INSTANCE_NAME=$(get_config "instanceName")
REGION=$(get_config "region")

echo "Building $INSTANCE_NAME in $REGION"

gcloud builds submit --config cloudbuild.yaml --substitutions=_REPO_NAME=$INSTANCE_NAME,_SERVICE_NAME=$INSTANCE_NAME,_REGION=$REGION
