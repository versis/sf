import os
import sys
import time
import json
import logging
from datetime import datetime

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)

# Get the log level from environment variable, defaulting to INFO
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
logger = logging.getLogger("sf-api")
logger.setLevel(numeric_level)

# Prevent duplicate logs by not propagating to root logger
logger.propagate = False

# Add custom request_id filter
class RequestIdFilter(logging.Filter):
    def __init__(self, request_id=None):
        super().__init__()
        self.request_id = request_id
    
    def filter(self, record):
        record.request_id = self.request_id if hasattr(self, 'request_id') else 'None'
        return True

# Add a console handler to ensure logs appear in the terminal
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(numeric_level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addFilter(RequestIdFilter())

def log(message, level="INFO", request_id=None, flush=True):
    """
    Log a message using Python's logging module.
    
    Parameters:
    -----------
    message : str
        The message to log
    level : str
        Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    request_id : str, optional
        A unique identifier for tracking the request across log messages
    flush : bool
        Whether to flush the stdout buffer immediately (ignored with logging module)
    """
    if request_id:
        # Update the filter with the request_id
        for handler in logger.handlers:
            for filter in handler.filters:
                if isinstance(filter, RequestIdFilter):
                    filter.request_id = request_id
    
    level_upper = level.upper()
    if level_upper == "DEBUG":
        logger.debug(message)
    elif level_upper == "INFO":
        logger.info(message)
    elif level_upper == "WARNING":
        logger.warning(message)
    elif level_upper == "ERROR":
        logger.error(message)
    elif level_upper == "CRITICAL":
        logger.critical(message)
    else:
        logger.info(message)
    
    if flush:
        for handler in logger.handlers:
            handler.flush()

def debug(message, request_id=None):
    log(message, level="DEBUG", request_id=request_id)

def info(message, request_id=None):
    log(message, level="INFO", request_id=request_id)

def warning(message, request_id=None):
    log(message, level="WARNING", request_id=request_id)

def error(message, request_id=None):
    log(message, level="ERROR", request_id=request_id)

def critical(message, request_id=None):
    log(message, level="CRITICAL", request_id=request_id) 