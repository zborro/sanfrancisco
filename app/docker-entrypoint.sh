#!/usr/bin/env bash
exec gunicorn --reload -k uvicorn.workers.UvicornWorker -c /gunicorn.conf.py main:app
