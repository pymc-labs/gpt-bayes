# Use miniconda as the base image
FROM continuumio/miniconda3:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Set the working directory
WORKDIR /app

# Copy requirements files
# COPY environment.yml .
COPY requirements.txt .

# Create conda environment and install packages
RUN conda create -n marketing_env -c conda-forge pymc-marketing && \
    conda run -n marketing_env pip install --no-cache-dir -r requirements.txt && \
    conda clean -afy

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "marketing_env", "/bin/bash", "-c"]

# Copy the rest of the application code
COPY . .

# Expose port 8080 (Cloud Run provides the PORT env variable at runtime)
EXPOSE 8080

# Run the application using Gunicorn in the conda environment
CMD exec conda run -n marketing_env gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 3 --timeout 3600 app:app