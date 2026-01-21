import logging
import sys
import os
from datetime import datetime

# Creates logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logging(level=logging.INFO):
    """
    Configures the root logger with a solid format including timestamps.
    Outputs to both Console (Stream) and File.
    """
    # Generate unique log filename based on timestamp
    log_filename = datetime.now().strftime(f"{LOG_DIR}/cv_processing_%Y-%m-%d.log")
    
    # Define the format: Timestamp | Level | Module | Message
    log_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates if re-initialized
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # 2. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # 3. File Handler (Append mode)
    file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    logging.info(f"Logging initialized. Writing to: {log_filename}")

def get_logger(name: str):
    """
    Returns a logger instance for a specific module.
    """
    return logging.getLogger(name)
