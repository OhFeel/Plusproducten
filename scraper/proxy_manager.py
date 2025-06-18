"""
proxy_manager.py - Manages proxies for the PLUS scraper
"""

import os
import random
import time
import requests
from typing import Dict, List, Optional, Union, Tuple
from functools import lru_cache
from dotenv import load_dotenv
from fp.fp import FreeProxy
from utils import logger, exponential_backoff

# Load environment variables
load_dotenv()

class ProxyManager:
    """
    Manages proxy rotation for web scraping
    Supports free proxies, ScraperAPI, Smartproxy, and AWS Gateway
    """
    
    def __init__(self):
        self.use_proxy = os.getenv("USE_PROXY", "false").lower() == "true"
        self.proxy_type = os.getenv("PROXY_TYPE", "free").lower()
        self.proxy_api_key = os.getenv("PROXY_API_KEY", "")
        self.proxy_list: List[Dict[str, Union[str, float]]] = []
        self.proxy_index = 0
        self.last_refresh_time = 0
        self.refresh_interval = 300  # 5 minutes refresh interval for free proxies
        
        if self.use_proxy:
            self.refresh_proxies()
    
    def refresh_proxies(self) -> None:
        """
        Refresh the list of proxies
        """
        if not self.use_proxy:
            return
        
        self.last_refresh_time = time.time()
        
        if self.proxy_type == "free":
            self._refresh_free_proxies()
        elif self.proxy_type == "scraperapi":
            # ScraperAPI handles rotation automatically
            pass
        elif self.proxy_type == "smartproxy":
            # Smartproxy credentials remain the same
            pass
        elif self.proxy_type == "aws":
            # AWS Gateway rotation is handled by requests-ip-rotator
            pass
        else:
            logger.warning(f"Unknown proxy type: {self.proxy_type}")
            
        logger.info(f"Refreshed proxies: {len(self.proxy_list)} {'proxies' if self.proxy_list else ''} available")
    
    def _refresh_free_proxies(self) -> None:
        """
        Refresh the list of free proxies using FreeProxy library
        """
        try:
            # Get a list of free proxies from various sources
            fp = FreeProxy(rand=True, timeout=2, https=True)
            new_proxies = []
            
            # Collect 10 proxies
            for _ in range(10):
                try:
                    proxy = fp.get()
                    if proxy and self._validate_proxy(proxy):
                        new_proxies.append({
                            "url": proxy,
                            "fail_count": 0,
                            "last_used": 0
                        })
                except Exception:
                    continue
            
            if new_proxies:
                self.proxy_list = new_proxies
                self.proxy_index = 0
            else:
                logger.warning("No valid free proxies found")
                
        except Exception as e:
            logger.error(f"Error refreshing free proxies: {e}")
    
    @exponential_backoff(max_retries=2, initial_delay=1.0)
    def _validate_proxy(self, proxy_url: str) -> bool:
        """
        Validate a proxy by testing a connection
        """
        try:
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            response = requests.get(
                "https://www.plus.nl", 
                proxies=proxies,
                timeout=3
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_proxy(self) -> Dict[str, str]:
        """
        Get a proxy for the current request
        """
        if not self.use_proxy:
            return {}
        
        # Check if we need to refresh the proxy list (for free proxies)
        if (self.proxy_type == "free" and 
            (time.time() - self.last_refresh_time > self.refresh_interval or not self.proxy_list)):
            self.refresh_proxies()
        
        if self.proxy_type == "free":
            return self._get_free_proxy()
        elif self.proxy_type == "scraperapi":
            return self._get_scraperapi_proxy()
        elif self.proxy_type == "smartproxy":
            return self._get_smartproxy_proxy()
        elif self.proxy_type == "aws":
            return {}  # AWS Gateway is handled separately
        else:
            return {}
    
    def _get_free_proxy(self) -> Dict[str, str]:
        """
        Get a free proxy from the list
        """
        if not self.proxy_list:
            return {}
        
        # Get the next proxy
        proxy_data = self.proxy_list[self.proxy_index]
        proxy_url = proxy_data["url"]
        
        # Update the proxy index for next time
        self.proxy_index = (self.proxy_index + 1) % len(self.proxy_list)
        
        # Update last used time
        proxy_data["last_used"] = time.time()
        
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    
    def _get_scraperapi_proxy(self) -> Dict[str, str]:
        """
        Get a ScraperAPI proxy
        """
        if not self.proxy_api_key:
            logger.warning("ScraperAPI key not found")
            return {}
        
        return {
            "http": f"http://scraperapi:{self.proxy_api_key}@proxy-server.scraperapi.com:8001",
            "https": f"http://scraperapi:{self.proxy_api_key}@proxy-server.scraperapi.com:8001"
        }
    
    def _get_smartproxy_proxy(self) -> Dict[str, str]:
        """
        Get a Smartproxy proxy with credentials
        """
        if not self.proxy_api_key or ":" not in self.proxy_api_key:
            logger.warning("Smartproxy credentials not properly configured")
            return {}
        
        username, password = self.proxy_api_key.split(":", 1)
        return {
            "http": f"http://{username}:{password}@gate.smartproxy.com:7000",
            "https": f"http://{username}:{password}@gate.smartproxy.com:7000"
        }
    
    def report_success(self, proxy_url: Optional[str] = None) -> None:
        """
        Report a successful request with a proxy
        """
        if not self.use_proxy or self.proxy_type != "free" or not proxy_url:
            return
        
        for proxy in self.proxy_list:
            if proxy["url"] == proxy_url:
                # Reset fail count on success
                proxy["fail_count"] = 0
                break
    
    def report_failure(self, proxy_url: Optional[str] = None) -> None:
        """
        Report a failed request with a proxy
        """
        if not self.use_proxy or self.proxy_type != "free" or not proxy_url:
            return
        
        for i, proxy in enumerate(self.proxy_list):
            if proxy["url"] == proxy_url:
                proxy["fail_count"] = proxy.get("fail_count", 0) + 1
                
                # Remove proxy if it fails too many times
                if proxy["fail_count"] >= 3:
                    del self.proxy_list[i]
                    # Adjust proxy_index if necessary
                    if i <= self.proxy_index and self.proxy_index > 0:
                        self.proxy_index -= 1
                break

# Create a singleton instance
proxy_manager = ProxyManager()
