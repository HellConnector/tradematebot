import logging
import os

MODE = os.getenv('MODE')

log_format = '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s'

formatter = logging.Formatter(fmt=log_format)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

log = logging.getLogger()
log.setLevel(logging.INFO)
log.addHandler(stream_handler)

if MODE == 'prod':
    file_handler = logging.FileHandler('tradematebot.log')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    log.addHandler(file_handler)
