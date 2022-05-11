preload_app = True
bind = '0.0.0.0:5060'
daemon = 'false'
# worker config
# worker_class = 'gevent'
workers = 4
threads = 4
worker_connections = 1200
accesslog = 'gunicorn_access.log'
errorlog = 'gunicorn_error.log'
loglevel = 'debug'
