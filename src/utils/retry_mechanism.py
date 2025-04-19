#!/usr/bin/env python3
"""
Retry handler utility for Crawl4AI scraper with exponential backoff
"""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast

logger = logging.getLogger('retry_handler')

T = TypeVar('T')

def retry_decorator(max_retries: int = 3, 
                   initial_backoff: float = 1.0,
                   backoff_multiplier: float = 2.0,
                   jitter: float = 0.1,
                   exceptions=(Exception,)):
    """
    Decorator for retry logic with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        backoff_multiplier: Multiplier for subsequent backoff times
        jitter: Random jitter factor to add to backoff
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Don't sleep after the last attempt
                    if attempt < max_retries:
                        # Calculate backoff with jitter
                        backoff_time = initial_backoff * (backoff_multiplier ** attempt)
                        jitter_amount = backoff_time * jitter * (2 * random.random() - 1)
                        sleep_time = backoff_time + jitter_amount
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed with error: {str(e)}. "
                            f"Retrying in {sleep_time:.2f} seconds..."
                        )
                        
                        await asyncio.sleep(sleep_time)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed. Last error: {str(e)}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    # Don't sleep after the last attempt
                    if attempt < max_retries:
                        # Calculate backoff with jitter
                        backoff_time = initial_backoff * (backoff_multiplier ** attempt)
                        jitter_amount = backoff_time * jitter * (2 * random.random() - 1)
                        sleep_time = backoff_time + jitter_amount
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed with error: {str(e)}. "
                            f"Retrying in {sleep_time:.2f} seconds..."
                        )
                        
                        time.sleep(sleep_time)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed. Last error: {str(e)}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        # Determine if the decorated function is async or sync
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class RateLimitException(Exception):
    """Exception raised when a rate limit is detected"""
    pass


class NetworkException(Exception):
    """Exception raised for network-related issues"""
    pass


def is_rate_limit_error(error: Exception) -> bool:
    """
    Check if an error is related to rate limiting
    
    Args:
        error: Exception to check
    
    Returns:
        True if rate limit related, False otherwise
    """
    error_str = str(error).lower()
    return any(term in error_str for term in [
        'rate limit', 
        'too many requests',
        '429',
        'throttl',
        'quota exceeded'
    ])


def is_network_error(error: Exception) -> bool:
    """
    Check if an error is related to network issues
    
    Args:
        error: Exception to check
    
    Returns:
        True if network related, False otherwise
    """
    error_str = str(error).lower()
    return any(term in error_str for term in [
        'connection', 
        'timeout',
        'timed out',
        'reset by peer',
        'network',
        'socket',
        'dns',
        'unreachable'
    ])


def classify_exception(exception: Exception) -> Exception:
    """
    Classify exception into more specific types for better retry handling
    
    Args:
        exception: Original exception
    
    Returns:
        Classified exception
    """
    if is_rate_limit_error(exception):
        return RateLimitException(str(exception))
    elif is_network_error(exception):
        return NetworkException(str(exception))
    return exception
