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
    gcloud compute ssh gpt-bayes --zone=us-central1-a --command "
        CONTAINER_ID=\$(docker ps --filter ancestor=us-central1-docker.pkg.dev/bayes-gpt/gpt-bayes/gpt-bayes:latest -q) && \
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
fi

echo "Deployment complete!"