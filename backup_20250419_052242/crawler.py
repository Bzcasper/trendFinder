#!/usr/bin/env python3
"""
Crawler service using Crawl4AI that extracts AI and LLM-related stories from websites.
This script replaces the previous Firecrawl JavaScript implementation.
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta  # Fixed import
import logging
import time
import colorama

# Initialize colorama for colored terminal output
colorama.init()

# Define colors for better logging
GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
RED = colorama.Fore.RED
CYAN = colorama.Fore.CYAN
RESET = colorama.Fore.RESET

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility modules
from utils.retryHandler import retry_decorator, classify_exception
from utils.crawlerConfig import get_config_manager
from utils.storyProcessor import get_story_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('crawler')

# Try importing Crawl4AI
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from pydantic import BaseModel, Field
except ImportError:
    logger.error(f"{RED}Crawl4AI not installed. Run 'pip install crawl4ai'{RESET}")
    sys.exit(1)

# Get config manager and story processor
config_manager = get_config_manager()
story_processor = get_story_processor()

# Define the schema for story extraction
class Story(BaseModel):
    headline: str = Field(..., description="Story or post headline")
    link: str = Field(..., description="A link to the post or story")
    date_posted: str = Field(..., description="The date the story or post was published")

class Stories(BaseModel):
    stories: list[Story] = Field(..., description="A list of today's AI or LLM-related stories")

@retry_decorator(max_retries=3, initial_backoff=2.0)
async def scrape_website(url: str, current_date: str) -> dict:
    """
    Scrape a website using Crawl4AI and extract AI/LLM-related stories
    
    Args:
        url: Website URL to scrape
        current_date: Current date in readable format
    
    Returns:
        Dict containing extracted stories or error information
    """
    start_time = time.time()
    logger.info(f"{CYAN}Scraping website: {url}{RESET}")
    
    # Get domain-specific configuration
    browser_cfg = config_manager.get_browser_config(url)
    run_cfg = config_manager.get_crawler_config(url)
    
    domain_settings = config_manager.get_domain_settings(url)
    retry_attempts = domain_settings.retry_count
    
    prompt = f"""
    Extract only today's AI or LLM related story or post headlines and links from the page.
    Today's date is {current_date}.
    
    For each story, extract:
    1. The headline/title of the story or post
    2. The full link to the story or post (make relative links absolute)
    3. The date the story was posted (in YYYY-MM-DD format)
    
    If there are no AI or LLM stories from today, return an empty array.
    Return only relevant AI/LLM stories, ignore everything else.
    
    Focus on these AI/ML topics: artificial intelligence, machine learning, LLMs, 
    large language models, generative AI, computer vision, neural networks, 
    transformers, OpenAI, Anthropic, Google AI, Microsoft AI, Hugging Face,
    foundation models, deep learning, natural language processing.
    """
    
    # Create LLM extraction strategy
    extraction_strategy = LLMExtractionStrategy(
        output_model=Stories,
        prompt=prompt
    )
    
    # Add extraction strategy to config
    run_cfg.extraction_strategy = extraction_strategy
    
    try:
        # Create crawler instance
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # Run the crawler on the URL
            result = await crawler.arun(url=url, config=run_cfg)
            
            if not result.success:
                logger.error(f"{RED}Failed to crawl {url}: {result.error_message}{RESET}")
                return {"stories": [], "error": result.error_message}
            
            # Extract and process stories
            if result.extracted_content and isinstance(result.extracted_content, dict) and "stories" in result.extracted_content:
                stories = result.extracted_content["stories"]
                logger.info(f"{GREEN}Found {len(stories)} stories from {url}{RESET}")
                
                # Make sure all links are absolute
                for story in stories:
                    if story.get("link") and not story["link"].startswith('http'):
                        # Convert relative URL to absolute
                        base_url = url.rstrip('/')
                        story["link"] = f"{base_url}/{story['link'].lstrip('/')}"
                
                elapsed_time = time.time() - start_time
                logger.info(f"{GREEN}Scraped {url} in {elapsed_time:.2f} seconds{RESET}")
                return {"stories": stories}
            else:
                # If no structured data was extracted, return empty stories
                logger.warning(f"{YELLOW}No stories extracted from {url}{RESET}")
                return {"stories": []}
    
    except Exception as e:
        # Classify and log the exception
        classified_error = classify_exception(e)
        logger.exception(f"{RED}Error scraping {url}: {str(classified_error)}{RESET}")
        return {"stories": [], "error": str(classified_error)}

@retry_decorator(max_retries=3, initial_backoff=2.0)
async def scrape_twitter(url: str, bearer_token: str) -> dict:
    """
    Scrape Twitter/X posts using Twitter API v2
    
    Args:
        url: Twitter profile URL (https://x.com/username)
        bearer_token: X/Twitter API bearer token
    
    Returns:
        Dict containing extracted tweets as stories
    """
    start_time = time.time()
    logger.info(f"{CYAN}Scraping Twitter account: {url}{RESET}")
    
    # Extract username from URL
    username = url.split('/')[-1]
    if not username:
        return {"stories": [], "error": "Invalid Twitter URL format"}
    
    # Get tweets from the last 24 hours
    # Fixed: Use timedelta correctly
    tweet_start_time = (datetime.now().replace(microsecond=0, second=0, minute=0) - 
                       timedelta(days=1)).isoformat() + "Z"
    
    # Construct the query and API URL - filter for tweets about AI/ML topics
    query = (f"from:{username} -is:retweet -is:reply (AI OR ML OR 'artificial intelligence' OR "
             f"'machine learning' OR 'large language model' OR LLM OR GPT OR 'generative AI')")
    encoded_query = query.replace(" ", "%20")
    encoded_start_time = tweet_start_time.replace(":", "%3A")
    api_url = f"https://api.x.com/2/tweets/search/recent?query={encoded_query}&max_results=15&start_time={encoded_start_time}"
    
    try:
        # Make request to Twitter API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {bearer_token}"
            }
            async with session.get(api_url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"{RED}Twitter API error: {response.status} - {error_text}{RESET}")
                    return {"stories": [], "error": f"Twitter API error: {response.status}"}
                
                tweets = await response.json()
                
                # Process tweets
                if tweets.get("meta", {}).get("result_count", 0) == 0:
                    logger.info(f"{YELLOW}No tweets found for username {username}{RESET}")
                    return {"stories": []}
                
                if not isinstance(tweets.get("data", []), list):
                    logger.error(f"{RED}Unexpected Twitter API response format{RESET}")
                    return {"stories": [], "error": "Unexpected Twitter API response format"}
                
                # Convert tweets to stories format
                stories = []
                for tweet in tweets.get("data", []):
                    stories.append({
                        "headline": tweet["text"],
                        "link": f"https://x.com/i/status/{tweet['id']}",
                        "date_posted": datetime.now().strftime("%Y-%m-%d"),  # Use current date
                        "source_type": "twitter"
                    })
                
                elapsed_time = time.time() - start_time
                logger.info(f"{GREEN}Found {len(stories)} tweets from {username} in {elapsed_time:.2f} seconds{RESET}")
                return {"stories": stories}
    
    except Exception as e:
        # Classify and log the exception
        classified_error = classify_exception(e)
        logger.exception(f"{RED}Error fetching tweets for {username}: {str(classified_error)}{RESET}")
        return {"stories": [], "error": str(classified_error)}

async def process_sources(sources: list[dict]) -> dict:
    """
    Process multiple sources in parallel with rate limiting
    
    Args:
        sources: List of source objects with identifier and type
    
    Returns:
        Dict with combined stories from all sources
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    all_stories = []
    errors = []
    
    # Check for required API keys
    twitter_token = os.environ.get("X_API_BEARER_TOKEN")
    
    # Filter sources by type
    website_sources = [s for s in sources if s["type"] == "website"]
    twitter_sources = [s for s in sources if s["type"] == "twitter"]
    
    # Skip Twitter sources if no API token
    if not twitter_token and twitter_sources:
        logger.warning(f"{YELLOW}No X_API_BEARER_TOKEN found - Twitter sources will be skipped{RESET}")
        twitter_sources = []
    
    # Sort website sources by priority
    website_sources_with_priority = []
    for source in website_sources:
        domain_settings = config_manager.get_domain_settings(source["identifier"])
        website_sources_with_priority.append((source, domain_settings.priority))
    
    # Sort by priority (highest first)
    website_sources_with_priority.sort(key=lambda x: x[1], reverse=True)
    website_sources = [s[0] for s in website_sources_with_priority]
    
    logger.info(f"{CYAN}Processing {len(website_sources)} website sources and {len(twitter_sources)} Twitter sources{RESET}")
    
    # Create a semaphore to limit concurrency
    max_concurrent = config_manager.settings.max_concurrent
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_scrape_website(source):
        """Run website scraper with concurrency limit"""
        async with semaphore:
            result = await scrape_website(source["identifier"], current_date)
            # Add source type to each story
            if "stories" in result and isinstance(result["stories"], list):
                for story in result["stories"]:
                    story["source_type"] = "website"
                    story["source_url"] = source["identifier"]
            
            # Apply rate limiting based on domain
            domain_settings = config_manager.get_domain_settings(source["identifier"])
            await asyncio.sleep(1.0 / domain_settings.rate_limit)
            return result, source
    
    async def bounded_scrape_twitter(source):
        """Run Twitter scraper with concurrency limit"""
        async with semaphore:
            result = await scrape_twitter(source["identifier"], twitter_token)
            # Add source info to each story
            if "stories" in result and isinstance(result["stories"], list):
                for story in result["stories"]:
                    story["source_url"] = source["identifier"]
            
            # Standard rate limit for Twitter API
            await asyncio.sleep(2.0)
            return result, source
    
    # Create tasks for all sources
    website_tasks = [bounded_scrape_website(source) for source in website_sources]
    twitter_tasks = [bounded_scrape_twitter(source) for source in twitter_sources]
    
    # Run all tasks
    all_tasks = website_tasks + twitter_tasks
    
    # Process results as they complete
    for future in asyncio.as_completed(all_tasks):
        try:
            result, source = await future
            
            if "error" in result:
                source_url = source["identifier"]
                logger.error(f"{RED}Error in result from {source_url}: {result['error']}{RESET}")
                errors.append({"source": source_url, "error": result["error"]})
            
            if "stories" in result and isinstance(result["stories"], list):
                all_stories.extend(result["stories"])
                logger.info(f"{GREEN}Added {len(result['stories'])} stories from {source['identifier']}{RESET}")
        except Exception as e:
            logger.exception(f"{RED}Unexpected error processing task: {str(e)}{RESET}")
            errors.append({"source": "unknown", "error": str(e)})
    
    # Process stories to filter, deduplicate, and enrich
    processed_stories = story_processor.process_stories(all_stories)
    
    logger.info(f"{CYAN}Total stories collected: {len(all_stories)}{RESET}")
    logger.info(f"{GREEN}After processing: {len(processed_stories)} unique, relevant stories{RESET}")
    
    return {
        "stories": processed_stories,
        "errors": errors
    }

def main():
    """
    Main entry point when script is called directly
    """
    # Read sources from command line argument (JSON string)
    if len(sys.argv) != 2:
        logger.error(f"{RED}Usage: python crawler.py '[{\"identifier\": \"https://example.com\", \"type\": \"website\"}]'{RESET}")
        sys.exit(1)
    
    try:
        sources = json.loads(sys.argv[1])
        result = asyncio.run(process_sources(sources))
        # Print result as JSON to stdout
        print(json.dumps(result))
    except json.JSONDecodeError:
        logger.error(f"{RED}Invalid JSON input{RESET}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"{RED}Error: {str(e)}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()