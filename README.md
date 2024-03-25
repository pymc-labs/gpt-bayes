# Deploying Your Application with Google Cloud Build

This repository provides the necessary configurations for deploying your application using Google Cloud Build.

## Deploy NGINX Reverse Proxy

To deploy the NGINX Reverse Proxy, navigate to the `nginx` directory and execute the following commands:

```bash
cd nginx
gcloud builds submit
```

This process will build a Docker container, push it to Google Artifact Registry (GAR), and deploy it to Cloud Run.

## Modify IP in NGINX Reverse Proxy

To update the IP address in the NGINX Reverse Proxy configuration, navigate to the `nginx` directory, edit the `nginx.conf` file, and modify the value of the IP in the `proxy_pass` directive:

```bash
cd nginx
# Open nginx.conf in your preferred text editor and update the IP
# Example: proxy_pass http://35.208.203.115:5000;
```

## Build and Push Webapp Container to Google Artifact Registry (GAR)

Execute the following command to build and push the web application container to Google Artifact Registry:

```bash
gcloud builds submit
```

This process will build a Docker container, push it to Google Artifact Registry (GAR).
This doesn't deploy to Google Compute Engine (GCE).

## Deploy to Google Compute Engine (GCE)

List Container-Optimized OS (COS) image names:

```bash
gcloud compute images list --project cos-cloud --no-standard-images
```

Update container:
```bash
gcloud compute ssh gpt-bayes --zone us-central1-a --command 'docker system prune -f -a'

gcloud compute instances update-container gpt-bayes \
  --zone=us-central1-a \
  --container-image=us-central1-docker.pkg.dev/bayes-gpt/gpt-bayes/gpt-bayes:latest
```

Deploy:

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
