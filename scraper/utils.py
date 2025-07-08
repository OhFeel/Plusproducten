"""
utils.py - Utility functions for the PLUS scraper
Contains header generation, logging setup, and retry mechanisms
"""

import os
import json
import time
import random
import logging
import colorlog
from pathlib import Path
from typing import Dict, Any, Optional, Union
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logger setup
def setup_logger(name: str = "plus_scraper", log_file: bool = True) -> logging.Logger:
    """
    Configure and return a logger with colored console output and optional file logging
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create colored console handler
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(f"logs/plus_scraper_{time.strftime('%Y%m%d')}.log")
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(file_handler)
    
    return logger

# Create the default logger
logger = setup_logger()

def get_plus_headers(referrer: str = "https://www.plus.nl") -> Dict[str, str]:
    """
    Generate headers for PLUS API requests
    """
    csrf_token = os.getenv("PLUS_CSRF_TOKEN", "")
    
    if not csrf_token:
        raise ValueError("PLUS_CSRF_TOKEN environment variable is required")
    
    return {
        "accept": "application/json",
        "accept-language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
        "content-type": "application/json; charset=UTF-8",
        "outsystems-locale": "nl-NL",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Not A(Brand\";v=\"8\", \"Chromium\";v=\"132\", \"Opera GX\";v=\"117\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-csrftoken": csrf_token,
        "Referer": referrer,
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

def save_to_retry(item: Dict[str, Any], reason: str = "unknown") -> None:
    """
    Save a failed item to retry.json for later processing
    """
    retry_file = Path("data/retry.json")
    retry_data = []
    
    # Create parent directory if it doesn't exist
    retry_file.parent.mkdir(exist_ok=True)
    
    # Load existing retry data if available
    if retry_file.exists():
        try:
            with open(retry_file, "r", encoding="utf-8") as f:
                retry_data = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Retry file was corrupted. Creating a new one.")
            retry_data = []
    
    # Add the current item with timestamp and reason
    retry_item = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": reason,
        "data": item
    }
    retry_data.append(retry_item)
    
    # Write back to the file
    with open(retry_file, "w", encoding="utf-8") as f:
        json.dump(retry_data, f, indent=2, ensure_ascii=False)

def exponential_backoff(max_retries: int = 3, initial_delay: float = 1.0,
                       factor: float = 2.0, jitter: bool = True):
    """
    Decorator for exponential backoff with optional jitter
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        raise
                    
                    # Calculate the next delay with optional jitter
                    if jitter:
                        delay_with_jitter = delay * (0.8 + random.random() * 0.4)  # +/- 20%
                    else:
                        delay_with_jitter = delay
                    
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {delay_with_jitter:.2f}s: {e}")
                    
                    # Sleep and increase delay for next attempt
                    time.sleep(delay_with_jitter)
                    delay *= factor
                    
        return wrapper
    return decorator

def extract_sku_from_url(url: str) -> Optional[str]:
    """
    Extract the SKU number from a PLUS product URL
    Example URL: https://www.plus.nl/product/plus-boerentrots-bbq-worst-tuinkruiden-krimp-280-g-553975
    """
    try:
        # Split by hyphens and get the last component which should be the SKU
        parts = url.strip('/').split('-')
        return parts[-1]
    except Exception:
        return None

def format_filename(filename: str) -> str:
    """
    Format a string to be a valid filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    return filename[:150]

def create_checkpoint(current_position: Union[int, str], total: Optional[Union[int, str]] = None,
                     checkpoint_type: str = "sitemap") -> None:
    """
    Save checkpoint information to a file
    """
    checkpoint_file = Path(f"data/checkpoint_{checkpoint_type}.json")
    checkpoint_file.parent.mkdir(exist_ok=True)
    
    checkpoint_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "current_position": current_position,
    }
    
    if total is not None:
        checkpoint_data["total"] = total
        checkpoint_data["progress_pct"] = float(current_position) / float(total) * 100 if float(total) > 0 else 0
    
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2)
    
    logger.debug(f"Checkpoint saved: {current_position}")

def load_checkpoint(checkpoint_type: str = "sitemap") -> Optional[Dict[str, Any]]:
    """
    Load checkpoint information from a file
    """
    checkpoint_file = Path(f"data/checkpoint_{checkpoint_type}.json")
    
    if not checkpoint_file.exists():
        return None
    
    try:
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning(f"Checkpoint file {checkpoint_file} is corrupted")
        return None
