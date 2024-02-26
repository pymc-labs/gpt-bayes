FROM mambaorg/micromamba:latest

ENV APP_HOME /app
ENV PORT 5000
ENV JAX_PLATFORM_NAME cpu

USER root
RUN apt-get update && DEBIAN_FRONTEND=“noninteractive” apt-get install -y --no-install-recommends \
    nginx \
    certbot \
    python3-certbot-nginx \
    sudo \
    && \
    rm -rf /var/lib/apt/lists/*

RUN chown -R $MAMBA_USER /var/lib/nginx /var/log/nginx

USER $MAMBA_USER

WORKDIR $APP_HOME

COPY . ./
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy the start script
COPY --chown=$MAMBA_USER:$MAMBA_USER start.sh $APP_HOME/start.sh
RUN chmod +x $APP_HOME/start.sh

ARG MAMBA_DOCKERFILE_ACTIVATE=1

# Expose the necessary ports
EXPOSE 80
EXPOSE 443
EXPOSE 5000
EXPOSE 8080

CMD ["./start.sh"]