#!/usr/bin/env python3
"""
Story processor utility for filtering, deduplicating, and enriching stories
"""

import re
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urlparse
import difflib

logger = logging.getLogger('story_processor')

class StoryProcessor:
    """
    Class for processing and enhancing scraped stories
    """
    
    def __init__(self, 
                min_headline_length: int = 20,
                max_headline_length: int = 200,
                similarity_threshold: float = 0.75,
                max_days_old: int = 2):
        """
        Initialize story processor
        
        Args:
            min_headline_length: Minimum length of headline to consider valid
            max_headline_length: Maximum length of headline to consider valid
            similarity_threshold: Threshold for considering stories as duplicates
            max_days_old: Maximum age of stories in days
        """
        self.min_headline_length = min_headline_length
        self.max_headline_length = max_headline_length
        self.similarity_threshold = similarity_threshold
        self.max_days_old = max_days_old
        
        # List of AI/ML keywords to filter for
        self.ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml', 
            'deep learning', 'neural network', 'llm', 'large language model',
            'generative ai', 'gpt', 'chatgpt', 'claude', 'gemini', 'llama',
            'mistral', 'transformer', 'diffusion', 'stable diffusion', 'midjourney',
            'openai', 'anthropic', 'google ai', 'microsoft ai', 'deepmind',
            'hugging face', 'nvidia', 'dall-e', 'natural language processing',
            'computer vision', 'reinforcement learning', 'rag', 'embeddings',
            'fine-tuning', 'prompt engineering', 'multimodal', 'foundation model'
        ]
        
        # Compile regex patterns for efficiency
        self.ai_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.ai_keywords) + r')\b', 
            re.IGNORECASE
        )
    
    def _clean_headline(self, headline: str) -> str:
        """
        Clean and normalize headline text
        
        Args:
            headline: Raw headline text
            
        Returns:
            Cleaned headline
        """
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', headline).strip()
        
        # Remove common prefixes
        prefixes = ["Breaking:", "Just in:", "New:", "Update:"]
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # Truncate if too long
        if len(cleaned) > self.max_headline_length:
            cleaned = cleaned[:self.max_headline_length - 3] + "..."
            
        return cleaned
    
    def _normalize_date(self, date_str: str) -> Optional[datetime]:
        """
        Normalize date string to datetime object
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Datetime object or None if invalid
        """
        try:
            # Try common formats
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%b %d, %Y",
                "%B %d, %Y",
                "%d %b %Y",
                "%d %B %Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
            # If all fail, assume it's a relative date or use current date
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if "today" in date_str.lower():
                return today
            elif "yesterday" in date_str.lower():
                return today - timedelta(days=1)
            elif "days ago" in date_str.lower():
                days = int(re.search(r'(\d+)\s+days ago', date_str.lower()).group(1))
                return today - timedelta(days=days)
            else:
                # Default to today
                return today
                
        except Exception as e:
            logger.warning(f"Could not parse date: {date_str} - {str(e)}")
            return None
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL format
        
        Args:
            url: Raw URL
            
        Returns:
            Normalized URL
        """
        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Remove tracking parameters
        parsed = urlparse(url)
        path = parsed.path
        
        # Remove trailing slash
        if path.endswith('/'):
            path = path[:-1]
            
        # Rebuild URL without query parameters (optional, may want to keep some)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{path}"
        
        return clean_url
    
    def _is_duplicate(self, story: Dict[str, Any], existing_stories: List[Dict[str, Any]]) -> bool:
        """
        Check if a story is a duplicate of existing stories
        
        Args:
            story: New story to check
            existing_stories: List of existing stories
            
        Returns:
            True if duplicate, False otherwise
        """
        # Check for exact URL match
        story_url = self._normalize_url(story.get('link', ''))
        for existing in existing_stories:
            existing_url = self._normalize_url(existing.get('link', ''))
            if story_url == existing_url:
                return True
                
        # Check for headline similarity
        story_headline = story.get('headline', '').lower()
        if not story_headline:
            return False
            
        for existing in existing_stories:
            existing_headline = existing.get('headline', '').lower()
            if not existing_headline:
                continue
                
            # Use difflib to calculate similarity ratio
            similarity = difflib.SequenceMatcher(None, story_headline, existing_headline).ratio()
            if similarity > self.similarity_threshold:
                return True
                
        return False
    
    def _is_relevant(self, story: Dict[str, Any]) -> bool:
        """
        Check if a story is relevant to AI/ML topics
        
        Args:
            story: Story to check
            
        Returns:
            True if relevant, False otherwise
        """
        # Check headline for AI keywords
        headline = story.get('headline', '').lower()
        if self.ai_pattern.search(headline):
            return True
            
        # If no keywords found, consider it not relevant
        return False
    
    def _is_valid_date(self, story: Dict[str, Any]) -> bool:
        """
        Check if a story date is valid and recent
        
        Args:
            story: Story to check
            
        Returns:
            True if valid and recent, False otherwise
        """
        date_str = story.get('date_posted', '')
        if not date_str:
            return False
            
        date_obj = self._normalize_date(date_str)
        if not date_obj:
            return False
            
        # Check if date is within max_days_old
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_old = (today - date_obj).days
        
        return days_old <= self.max_days_old
    
    def process_stories(self, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of stories - filter, deduplicate, and enrich
        
        Args:
            stories: List of raw stories
            
        Returns:
            Processed stories
        """
        processed_stories = []
        
        for story in stories:
            # Skip if already processed
            if self._is_duplicate(story, processed_stories):
                continue
            
            # Clean headline
            if 'headline' in story:
                story['headline'] = self._clean_headline(story['headline'])
                
                # Skip if headline is too short
                if len(story['headline']) < self.min_headline_length:
                    continue
            
            # Normalize URL
            if 'link' in story:
                story['link'] = self._normalize_url(story['link'])
                
            # Skip if not relevant to AI/ML
            if not self._is_relevant(story):
                continue
                
            # Skip if date is too old
            if not self._is_valid_date(story):
                continue
                
            # Add source domain as metadata
            if 'link' in story:
                domain = urlparse(story['link']).netloc
                story['source_domain'] = domain
            
            # Add story to processed list
            processed_stories.append(story)
            
        # Sort stories by date (newest first)
        processed_stories.sort(
            key=lambda x: self._normalize_date(x.get('date_posted', '')) or datetime.now(),
            reverse=True
        )
        
        return processed_stories

# Create a singleton instance
story_processor = StoryProcessor()

def get_story_processor() -> StoryProcessor:
    """
    Get the singleton story processor instance
    
    Returns:
        StoryProcessor instance
    """
    return story_processor
