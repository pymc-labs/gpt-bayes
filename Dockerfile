FROM mambaorg/micromamba:latest

ENV APP_HOME=/app
ENV PORT=5000
ENV JAX_PLATFORM_NAME=cpu

WORKDIR $APP_HOME

COPY . ./
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes && \
    mkdir -p /opt/conda/var/db && \
    chown $MAMBA_USER:$MAMBA_USER /opt/conda/var/db && \
    mkdir -p /opt/conda/var/db/redis && \
    chown $MAMBA_USER:$MAMBA_USER /opt/conda/var/db/redis && \
    chmod 750 /opt/conda/var/db/redis

# Copy the start script
COPY --chown=$MAMBA_USER:$MAMBA_USER start.sh $APP_HOME/start.sh
RUN chmod +x $APP_HOME/start.sh

ARG MAMBA_DOCKERFILE_ACTIVATE=1

EXPOSE 5000
EXPOSE 8080

CMD ["./start.sh"]