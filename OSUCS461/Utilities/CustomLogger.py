import os
import time
import logging
from OSUCS461.Config import env
from logging.handlers import RotatingFileHandler

loki_on = False

app_name = "HP-API"

def custom_logger(name, log_file, level=logging.DEBUG):
	current_dir = os.path.abspath(os.path.dirname(__file__))

	project_root = os.path.dirname(current_dir)

	logs_dir = os.path.join(project_root, "Logs")

	if not os.path.exists(logs_dir):
		os.makedirs(logs_dir)

	log_file_path = os.path.join(logs_dir, log_file)

	logger = logging.getLogger(name)
	logger.setLevel(level)

	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - '+f'{app_name} - {env} - '+'%(message)s')
	formatter.converter = time.gmtime


	file_handler = RotatingFileHandler(log_file_path, maxBytes=25*1024*1024, backupCount=5)
	stream_handler = logging.StreamHandler()

	if env == "local":
		file_handler.setLevel(logging.DEBUG)
		stream_handler.setLevel(logging.DEBUG)
	else:
		file_handler.setLevel(logging.DEBUG)
		stream_handler.setLevel(logging.DEBUG)

	file_handler.setFormatter(formatter)

	if not logger.handlers:
		logger.addHandler(file_handler)
		stream_handler.setFormatter(formatter)
		logger.addHandler(stream_handler)

	return logger
