#!/bin/bash

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
    gcloud builds submit
    
    echo "Cleaning up docker system..."
    gcloud compute ssh gpt-bayes --zone us-central1-a --command 'docker system prune -f -a'

    echo "Updating container..."
    gcloud compute instances update-container gpt-bayes \
        --zone=us-central1-a \
        --container-image=us-central1-docker.pkg.dev/bayes-gpt/gpt-bayes/gpt-bayes:latest
else
    echo "Copying new files and restarting application..."
    # First, copy files to the instance
    gcloud compute scp --zone=us-central1-a --recurse ./*.py gpt-bayes:/tmp/
    
    # Then copy files into the container and restart services
    gcloud compute ssh gpt-bayes --zone=us-central1-a --command '
        CONTAINER_ID=$(docker ps --filter ancestor=us-central1-docker.pkg.dev/bayes-gpt/gpt-bayes/gpt-bayes:latest -q) && \
        if [ -z "$CONTAINER_ID" ]; then
            echo "Error: Could not find running container"
            exit 1
        fi && \
        echo "Updating container: $CONTAINER_ID" && \
        docker cp /tmp/*.py $CONTAINER_ID:/app/ && \
        docker exec $CONTAINER_ID pkill -f "celery" && \
        docker exec $CONTAINER_ID pkill -f "gunicorn" && \
        docker exec -w /app $CONTAINER_ID ./start.sh
    '
fi

echo "Deployment complete!"