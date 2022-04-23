FROM python:3.10-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

COPY ./gunicorn.conf.py /gunicorn.conf.py

COPY ./src /app
WORKDIR /app

CMD ["/docker-entrypoint.sh"]
