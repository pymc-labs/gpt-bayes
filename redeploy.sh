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
    # Copy new files to the instance
    gcloud compute scp --zone=us-central1-a --recurse ./*.py gpt-bayes:/tmp/
    
    # Copy files and restart services
    gcloud compute ssh gpt-bayes --zone=us-central1-a --command '
        sudo cp /tmp/*.py /app/ && \
        sudo pkill -f "celery" && \
        sudo pkill -f "gunicorn" && \
        cd /app && \
        ./start.sh
    '
fi

echo "Deployment complete!"