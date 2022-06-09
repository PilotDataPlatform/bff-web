FROM python:3.7-buster

RUN groupadd --gid 1004 deploy \
    && useradd --home-dir /home/deploy --create-home --uid 1004 \
        --gid 1004 --shell /bin/sh --skel /dev/null deploy
WORKDIR /home/deploy
RUN wget https://dl.min.io/client/mc/release/linux-amd64/mc -P /usr/local/bin

RUN chmod +x /usr/local/bin/mc

RUN apt-get update && apt-get install libsasl2-dev python-dev libldap2-dev libssl-dev -y && rm -rf /var/lib/apt/lists/*

USER deploy
RUN pip install --no-cache-dir poetry==1.1.12
COPY poetry.lock pyproject.toml ./
RUN python -m poetry config virtualenvs.create false
RUN python -m poetry install --no-dev --no-root --no-interaction


USER root
COPY .  ./
RUN chown -R deploy:deploy /home/deploy
RUN chmod +x /home/deploy/gunicorn_starter.sh

USER deploy
ENV PATH="/home/deploy/.local/bin:${PATH}"
ENV MINIO_USERNAME=minioadmin
ENV MINIO_PASSWORD=minioadmin
ENV MINIO_URL=http://minio.minio:9000
CMD ["sh", "-c", "mc alias set minio $MINIO_URL $MINIO_USERNAME $MINIO_PASSWORD && ./gunicorn_starter.sh"]
