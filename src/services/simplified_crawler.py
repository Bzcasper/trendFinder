#!/usr/bin/env python3
"""
Simplified crawler that doesn't require Crawl4AI - just returns dummy data
"""

import json
import sys
import os
from datetime import datetime
import logging
import time
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('simple_crawler')

# ANSI colors for terminal output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
RESET = '\033[0m'

def generate_dummy_stories(sources):
    """
    Generate dummy stories for demonstration purposes
    """
    all_stories = []
    
    # Dummy headlines for each domain type
    ai_headlines = [
        "New Research Shows Breakthrough in Large Language Model Efficiency",
        "OpenAI Announces GPT-5 Development Progress",
        "Anthropic Releases Claude 3.7 with Improved Reasoning",
        "Google DeepMind's Latest AI System Can Solve Complex Math Problems",
        "Meta's AI Research Team Publishes Paper on Multimodal Learning",
        "Microsoft Azure Expands AI Capabilities with New Services",
        "Researchers Develop More Energy-Efficient Neural Networks",
        "Hugging Face Introduces New Tools for Model Fine-Tuning",
        "AI Safety Research Receives Major Funding Boost",
        "Computer Vision Advances Enable New Medical Imaging Applications"
    ]
    
    # Generate stories based on source type
    for source in sources:
        source_type = source.get("type", "")
        identifier = source.get("identifier", "")
        domain = identifier.split("//")[-1].split("/")[0]
        
        # Number of stories to generate per source (random)
        num_stories = random.randint(1, 3)
        
        logger.info(f"{CYAN}Generating {num_stories} dummy stories for {identifier}{RESET}")
        
        for i in range(num_stories):
            # Select a random headline
            headline = random.choice(ai_headlines)
            
            # Create a story
            story = {
                "headline": headline,
                "link": f"https://{domain}/article/{int(time.time())}-{i}",
                "date_posted": datetime.now().strftime("%Y-%m-%d"),
                "source_type": source_type,
                "source_url": identifier,
                "source_domain": domain
            }
            
            all_stories.append(story)
            
    logger.info(f"{GREEN}Generated {len(all_stories)} total dummy stories{RESET}")
    return all_stories

def main():
    """
    Main entry point when script is called directly
    """
    # Read sources from command line argument (JSON string)
    if len(sys.argv) != 2:
        # Fixed the string escaping for double quotes in the f-string
        usage_msg = f"{RED}Usage: python simplified_crawler.py '[{{\"identifier\": \"https://example.com\", \"type\": \"website\"}}]'{RESET}"
        logger.error(usage_msg)
        sys.exit(1)
    
    try:
        # Handle Windows command-line escaping issues
        arg = sys.argv[1]
        # Replace escaped quotes if needed
        if '\\\"' in arg:
            arg = arg.replace('\\\"', '"')
        
        # Strip surrounding quotes if they exist
        if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
            arg = arg[1:-1]
            
        # Debug the input
        logger.info(f"{CYAN}Received argument: {arg[:100]}...{RESET}")
        
        # Parse JSON
        sources = json.loads(arg)
        logger.info(f"{GREEN}Successfully parsed JSON with {len(sources)} sources{RESET}")
        
        # Generate dummy stories
        stories = generate_dummy_stories(sources)
        
        # Create result object
        result = {
            "stories": stories,
            "errors": []
        }
        
        # Print result as JSON to stdout
        print(json.dumps(result))
    except json.JSONDecodeError as e:
        logger.error(f"{RED}Invalid JSON input: {str(e)}{RESET}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"{RED}Error: {str(e)}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()