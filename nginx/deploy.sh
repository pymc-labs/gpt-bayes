#!/bin/bash

# Validate environment argument
if [ "$1" != "production" ] && [ "$1" != "development" ]; then
    echo "Error: Environment must be specified as either 'production' or 'development'"
    echo "Usage: $0 <environment>"
    exit 1
fi

ENVIRONMENT=$1

# Function to read config value
get_nginx_config() {
    local key=$1
    yq ".$ENVIRONMENT.nginx.$key" ../config.yaml | tr -d '"'
}

# Get configuration values
SERVER_NAME=$(get_nginx_config "serverName")
IP_ADDRESS=$(get_nginx_config "ipAddress")
PORT=$(get_nginx_config "port")
REPO_NAME=$(get_nginx_config "repoName")
SERVICE_NAME=$(get_nginx_config "serviceName")
REGION=$(get_nginx_config "region")

# Replace placeholders in nginx.conf.template
sed -e "s/\${SERVER_NAME}/$SERVER_NAME/g" \
    -e "s/\${IP_ADDRESS}/$IP_ADDRESS/g" \
    -e "s/\${PORT}/$PORT/g" nginx.conf.template > nginx.conf


# Deploy
gcloud builds submit --config cloudbuild.yaml --substitutions=_REPO_NAME=$REPO_NAME,_SERVICE_NAME=$SERVICE_NAME,_REGION=$REGION

# Clean up
rm nginx.conf
