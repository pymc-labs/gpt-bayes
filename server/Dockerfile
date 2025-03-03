FROM mambaorg/micromamba:latest

ENV APP_HOME=/app
ENV PORT=5000
ENV JAX_PLATFORM_NAME=cpu

ARG API_KEY
ARG MODEL_BUCKET
ARG CLOUD_RUN_URL

ENV API_KEY=$API_KEY \
    MODEL_BUCKET=$MODEL_BUCKET \
    CLOUD_RUN_URL=$CLOUD_RUN_URL

WORKDIR $APP_HOME

COPY *.py /app/
COPY *.json /app/
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes && \
    mkdir -p /opt/conda/var/db && \
    chown $MAMBA_USER:$MAMBA_USER /opt/conda/var/db && \
    mkdir -p /opt/conda/var/db/redis && \
    chown -R $MAMBA_USER:$MAMBA_USER /opt/conda/var/db/redis && \
    chmod -R 770 /opt/conda/var/db/redis

# Copy the start script
COPY --chown=$MAMBA_USER:$MAMBA_USER start.sh $APP_HOME/start.sh
RUN chmod +x $APP_HOME/start.sh

ARG MAMBA_DOCKERFILE_ACTIVATE=1

EXPOSE 5000
# EXPOSE 8080

CMD ["./start.sh"]