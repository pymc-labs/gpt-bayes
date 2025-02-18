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
ZONE=$(get_config "zone")

# Function to check if rebuild is needed
should_rebuild() {
    read -p "Did you modify Dockerfile, environment.yml or other dependencies? (y/N): " answer
    case ${answer:0:1} in
        y|Y )
            return 0
        ;;
        * )
            return 1
        ;;
    esac
}

if should_rebuild; then
    echo "Rebuilding container..."
    ./build.sh $ENVIRONMENT
    
    echo "Cleaning up docker system..."
    gcloud compute ssh "$INSTANCE_NAME" --zone "$ZONE" --command 'docker system prune -f -a'

    echo "Updating container..."
    gcloud compute instances update-container "$INSTANCE_NAME" \
        --zone="$ZONE" \
        --container-image=$REGION-docker.pkg.dev/bayes-gpt/$INSTANCE_NAME/$INSTANCE_NAME:latest
else
    echo "Copying new files and restarting application..."
    # First, copy files to the instance
    gcloud compute scp --zone="$ZONE" --recurse ./*.py "$INSTANCE_NAME":/tmp/
    
    # Then copy files into the container and restart services
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command "
        CONTAINER_ID=\$(docker ps --filter ancestor=$REGION-docker.pkg.dev/bayes-gpt/$INSTANCE_NAME/$INSTANCE_NAME:latest -q) && \
        if [ -z \"\$CONTAINER_ID\" ]; then
            echo \"Error: Could not find running container\"
            exit 1
        fi && \
        echo \"Updating container: \$CONTAINER_ID\" && \
        cd /tmp && \
        for file in *.py; do
            [ -f \"\$file\" ] && docker cp \"\$file\" \"\$CONTAINER_ID:/app/\"
        done && \
        # Kill existing processes using pkill instead of killall
        docker exec \$CONTAINER_ID micromamba run -n base pkill -9 celery || true && \
        docker exec \$CONTAINER_ID micromamba run -n base pkill -9 gunicorn || true && \
        # Start the application in detached mode
        docker exec -d -w /app \$CONTAINER_ID micromamba run -n base ./start.sh
    "

    # Restart the container
    echo "Restarting container..."
    gcloud compute ssh "$INSTANCE_NAME" --zone="$ZONE" --command "docker restart \$(docker ps --filter ancestor=$REGION-docker.pkg.dev/bayes-gpt/$INSTANCE_NAME/$INSTANCE_NAME:latest -q)"
fi

echo "Deployment complete!"
