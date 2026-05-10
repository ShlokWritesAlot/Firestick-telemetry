import logging
import os
import time
from datetime import datetime
from scripts.config import LOG_DIR

def setup_logging(name: str = "EdgePulse"):
    """
    Configures robust logging for the application.
    """
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Console Handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)

    # File Handler
    log_filename = f"{name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    f_handler = logging.FileHandler(os.path.join(LOG_DIR, log_filename))
    f_handler.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger

def get_timestamp():
    """Returns high-precision timestamp string."""
    return datetime.now().isoformat()

def get_unix_timestamp():
    """Returns unix timestamp."""
    return time.time()
