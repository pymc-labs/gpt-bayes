## Cloud Run Deployment

### Build and Push Docker Image

Build and push the Docker image to Google Artifact Registry:
```bash
./build.sh production # Build and publish to production
./build.sh development # Build and publish to development
```

### Cloud Run Deployment

Deploy the Cloud Run service:
```bash
cd cloudrun
./deploy.sh production # Deploy to production
./deploy.sh development # Deploy to development
```

## Cloud Run Testing

```bash
cd cloudrun
python test_cloudrun_fit_mmm.py
```


