import multiprocessing
from os import getenv


# this can be dangerous outside docker!
host = getenv('HOST', '0.0.0.0')
port = getenv('PORT', '8000')

bind = f'{host}:{port}'
workers = 2
accesslog = '-'
worker_tmp_dir = '/dev/shm'
