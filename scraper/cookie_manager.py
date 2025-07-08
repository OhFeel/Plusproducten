"""
cookie_manager.py - Manages cookies for the PLUS API requests
"""

import os
import json
import time
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from utils import logger

# Load environment variables
load_dotenv()

class CookieManager:
    """
    Manages cookies for API requests to PLUS
    """
    
    def __init__(self):
        self.cookies = {}
        self.cookie_file = Path("data/cookies.json")
        self.load_cookies()
    
    def load_cookies(self) -> Dict[str, str]:
        """
        Load cookies from .env file or cached cookie file
        """
        # First try to load from .env
        cookies = {}
        
        # Check if we have cookies in environment variables
        cookie_count = int(os.getenv("COOKIE_COUNT", "0"))
        
        if cookie_count > 0:
            # Load cookies from environment variables
            for key in os.environ:
                if key.startswith("COOKIE_"):
                    # Skip the counter
                    if key == "COOKIE_COUNT":
                        continue
                    
                    # Extract cookie name and value
                    cookie_name = key[7:].lower().replace('_', '-')  # Remove COOKIE_ prefix and convert to lowercase
                    cookies[cookie_name] = os.getenv(key, "")
            
            logger.debug(f"Loaded {len(cookies)} cookies from environment variables")
        
        # If no cookies in .env, try to load from cache file
        elif self.cookie_file.exists():
            try:
                with open(self.cookie_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                logger.debug(f"Loaded {len(cookies)} cookies from cache file")
            except json.JSONDecodeError:
                logger.warning("Cookie cache file is corrupted")
        
        # Use minimal defaults if no cookies found
        if not cookies:
            logger.warning("No cookies found! Please configure cookies in .env file or run cookie setup.")
            logger.info("See COOKIES.md for setup instructions")
            # Use minimal required cookies - these need to be updated with real values
            cookies = {
                "SSLB": "1",
                "plus_cookie_level": "3"
            }
        
        self.cookies = cookies
        return cookies
    
    def save_cookies(self, cookies: Dict[str, str]) -> None:
        """
        Save cookies to cache file
        """
        try:
            self.cookie_file.parent.mkdir(exist_ok=True)
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            logger.debug(f"Saved {len(cookies)} cookies to cache file")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
    
    def extract_cookies_from_response(self, response) -> Dict[str, str]:
        """
        Extract cookies from a response
        """
        if not hasattr(response, 'cookies'):
            return {}
        
        new_cookies = {}
        for name, value in response.cookies.items():
            new_cookies[name] = value
        
        # Update our cookie store with any new cookies
        self.cookies.update(new_cookies)
        
        # Save the updated cookies to cache
        if new_cookies:
            self.save_cookies(self.cookies)
            logger.debug(f"Updated {len(new_cookies)} cookies from response")
        
        return new_cookies
    
    def get_cookies(self) -> Dict[str, str]:
        """
        Get the current cookie set
        """
        return self.cookies

# Create a singleton instance
cookie_manager = CookieManager()
