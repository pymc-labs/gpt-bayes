FROM mambaorg/micromamba:latest

ENV APP_HOME /app

ENV PORT 5000

WORKDIR $APP_HOME

COPY . ./
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml

RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1

CMD gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
