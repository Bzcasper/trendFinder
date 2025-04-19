#!/usr/bin/env python3
"""
Configuration manager for Crawl4AI with adaptive settings
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode

logger = logging.getLogger('crawler_config')

class DomainSettings(BaseModel):
    """Domain-specific crawler settings"""
    wait_time: int = Field(default=2000, description="Wait time in ms after page load")
    rate_limit: float = Field(default=1.0, description="Requests per second")
    retry_count: int = Field(default=3, description="Number of retries for this domain")
    css_selector: Optional[str] = Field(default=None, description="Domain-specific CSS selector")
    excluded_selectors: List[str] = Field(default_factory=list, description="Selectors to exclude")
    user_agent: Optional[str] = Field(default=None, description="Custom user agent")
    js_snippet: Optional[str] = Field(default=None, description="Custom JS to execute")
    priority: int = Field(default=0, description="Priority (higher = more important)")
    

class CrawlerSettings(BaseModel):
    """Global crawler settings"""
    default_browser_type: str = Field(default="chromium", description="Browser type")
    default_headless: bool = Field(default=True, description="Run in headless mode")
    default_timeout: int = Field(default=60000, description="Default timeout in ms")
    default_rate_limit: float = Field(default=0.5, description="Default requests per second")
    max_concurrent: int = Field(default=5, description="Max concurrent requests")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    log_level: str = Field(default="INFO", description="Logging level")
    proxy: Optional[str] = Field(default=None, description="Proxy server")
    domains: Dict[str, DomainSettings] = Field(default_factory=dict, description="Domain-specific settings")
    

class ConfigManager:
    """Manager for crawler configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to JSON configuration file (optional)
        """
        # Default config file is crawler_config.json in current directory
        if config_path is None:
            config_path = os.environ.get(
                'CRAWLER_CONFIG_PATH', 
                str(Path.cwd() / 'crawler_config.json')
            )
        
        self.config_path = config_path
        self.settings = self._load_config()
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.settings.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_config(self) -> CrawlerSettings:
        """
        Load configuration from file or use defaults
        
        Returns:
            CrawlerSettings object
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    return CrawlerSettings.parse_obj(config_data)
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return CrawlerSettings()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}, using defaults")
            return CrawlerSettings()
    
    def save_config(self) -> None:
        """
        Save current configuration to file
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.settings.dict(), f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def get_domain_settings(self, url: str) -> DomainSettings:
        """
        Get domain-specific settings for a URL
        
        Args:
            url: URL to get settings for
            
        Returns:
            DomainSettings for the domain
        """
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Check for exact domain match
        if domain in self.settings.domains:
            return self.settings.domains[domain]
        
        # Check for subdomain matches
        for config_domain, settings in self.settings.domains.items():
            if domain.endswith(f".{config_domain}") or config_domain.endswith(f".{domain}"):
                return settings
        
        # No match, create default settings
        default_settings = DomainSettings()
        
        # Add to domains dict for future reference
        self.settings.domains[domain] = default_settings
        
        return default_settings
    
    def get_browser_config(self, url: Optional[str] = None) -> BrowserConfig:
        """
        Get browser configuration for a URL
        
        Args:
            url: URL to get configuration for (optional)
            
        Returns:
            BrowserConfig object
        """
        # Start with default settings
        config_kwargs = {
            "browser_type": self.settings.default_browser_type,
            "headless": self.settings.default_headless,
            "timeout": self.settings.default_timeout,
            "proxy": self.settings.proxy
        }
        
        # Apply domain-specific settings if URL provided
        if url:
            domain_settings = self.get_domain_settings(url)
            if domain_settings.user_agent:
                config_kwargs["user_agent"] = domain_settings.user_agent
        
        return BrowserConfig(**config_kwargs)
    
    def get_crawler_config(self, url: str) -> CrawlerRunConfig:
        """
        Get crawler configuration for a URL
        
        Args:
            url: URL to get configuration for
            
        Returns:
            CrawlerRunConfig object
        """
        domain_settings = self.get_domain_settings(url)
        
        cache_mode = CacheMode.USE_CACHE if self.settings.cache_enabled else CacheMode.BYPASS
        
        config_kwargs = {
            "cache_mode": cache_mode,
            "wait_for_timeout": domain_settings.wait_time,
            "js_snippet": domain_settings.js_snippet,
        }
        
        # Add CSS selector if specified
        if domain_settings.css_selector:
            config_kwargs["css_selector"] = domain_settings.css_selector
        
        return CrawlerRunConfig(**config_kwargs)


# Create singleton instance
config_manager = ConfigManager()

def get_config_manager() -> ConfigManager:
    """
    Get the singleton config manager instance
    
    Returns:
        ConfigManager instance
    """
    return config_manager
