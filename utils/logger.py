import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name=__name__):
    """Setup comprehensive logging system"""
    
    # Create logs directory
    logs_dir = Path('./logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler for debug logs
    debug_handler = logging.FileHandler(
        f'logs/debug_{datetime.now().strftime("%Y%m%d")}.log',
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    debug_handler.setFormatter(debug_format)
    
    # File handler for error logs
    error_handler = logging.FileHandler(
        f'logs/error_{datetime.now().strftime("%Y%m%d")}.log',
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_format)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(error_handler)
    
    return logger
