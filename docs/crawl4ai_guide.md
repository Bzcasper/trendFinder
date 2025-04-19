# Understanding the Crawl4AI Integration

This document explains how we've integrated Crawl4AI into our Trend Finder application, the benefits of this approach, and how to customize the scraping behavior.

## What is Crawl4AI?

Crawl4AI is an open-source Python web crawler specifically designed for AI applications. It offers several advantages over traditional scraping libraries:

1. **Browser Automation**: Uses Playwright to control real browsers, enabling extraction from JavaScript-heavy sites.

2. **Asynchronous Processing**: Efficiently crawls multiple sites in parallel.

3. **AI-Powered Extraction**: Can use LLMs to identify and extract structured data.

4. **Clean Output Generation**: Converts web content to clean, LLM-friendly formats like markdown.

## Our Integration Architecture

Our implementation follows a hybrid approach:

1. **Python Crawler Service**: `crawler.py` contains the Crawl4AI implementation for web scraping and Twitter API integration.

2. **TypeScript Interface**: `scrapeSources.ts` provides a Node.js interface to the Python service using child processes.

3. **Modal API for Analysis**: We use a Modal-hosted LLM for analyzing the scraped content.

4. **Notification Service**: Sends the final results to Slack or Discord.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  getCronSources │─────▶│  scrapeSources  │─────▶│  generateDraft  │
│    (TypeScript) │      │   (TypeScript)  │      │   (TypeScript)  │
└─────────────────┘      └────────┬────────┘      └────────┬────────┘
                                  │                         │
                                  ▼                         ▼
                         ┌─────────────────┐      ┌─────────────────┐
                         │    crawler.py   │      │    Modal API    │
                         │     (Python)    │      │   (Inference)   │
                         └─────────────────┘      └────────┬────────┘
                                                           │
                                                           ▼
                                                  ┌─────────────────┐
                                                  │    sendDraft    │
                                                  │   (TypeScript)  │
                                                  └─────────────────┘
```

## Key Features of Our Crawl4AI Implementation

### 1. Browser-Based Scraping

We use Playwright through Crawl4AI to render JavaScript, wait for content to load, and handle modern web applications:

```python
browser_cfg = BrowserConfig(
    headless=True,         # Run without visible UI
    verbose=False,         # Minimize console output
    timeout=60000          # 60 seconds timeout
)
```

### 2. Asynchronous Processing

We leverage Python's asyncio to process multiple sources in parallel:

```python
# Create tasks for all sources
website_tasks = [scrape_website(source["identifier"], current_date) for source in website_sources]
twitter_tasks = [scrape_twitter(source["identifier"], twitter_token) for source in twitter_sources]

# Run all tasks concurrently
all_tasks = website_tasks + twitter_tasks
results = await asyncio.gather(*all_tasks, return_exceptions=True)
```

### 3. Structured Data Extraction

We use Crawl4AI's LLM-based extraction to obtain structured data:

```python
extraction_strategy = LLMExtractionStrategy(
    output_model=Stories,
    prompt=prompt
)
```

### 4. TypeScript-Python Integration

We use Node.js child processes to bridge TypeScript and Python:

```typescript
const execPromise = promisify(exec);
const { stdout, stderr } = await execPromise(`python ${crawlerPath} '${sourcesJson}'`);
const result = JSON.parse(stdout);
```

## Customizing the Crawler

### Adjusting Browser Behavior

In `crawler.py`, you can modify the `BrowserConfig` to change how the browser operates:

```python
browser_cfg = BrowserConfig(
    headless=False,           # Set to False to see the browser UI (for debugging)
    viewport_width=1920,      # Set wider viewport for certain sites
    viewport_height=1080,     # Increase height for scrolling pages
    proxy="http://user:pass@myproxy:8080",  # Use a proxy if needed
    user_agent="Custom User Agent String",   # Customize user agent
    timeout=120000            # Increase timeout for slower sites (in ms)
)
```

### Modifying Extraction Parameters

Customize the `CrawlerRunConfig` to control content extraction:

```python
run_cfg = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,  # Always fetch fresh content
    word_count_threshold=30,      # Ignore sections with fewer than 30 words
    excluded_tags=["nav", "footer", "aside"],  # Skip these HTML tags
    remove_overlay_elements=True,  # Remove cookie/popup overlays
    wait_for="css:.content-loaded",  # Wait for specific elements
    wait_for_timeout=20000        # Wait up to 20 seconds for content
)
```

### Customizing the LLM Extraction

You can adjust the prompt used for extraction to target specific content:

```python
prompt = f"""
Extract only today's AI or LLM related story or post headlines from the page.
Focus on stories about these specific topics: {', '.join(specific_topics)}
For each story, extract:
1. The headline/title
2. The full link
3. The publication date
"""
```

### Adding Custom Processors

You can extend the crawler with custom post-processing functions:

```python
def process_story(story):
    """Add custom processing for each story"""
    # Clean up headline
    story["headline"] = story["headline"].strip()
    
    # Ensure date is in correct format
    try:
        parsed_date = dateutil.parser.parse(story["date_posted"])
        story["date_posted"] = parsed_date.strftime("%Y-%m-%d")
    except:
        story["date_posted"] = datetime.now().strftime("%Y-%m-%d")
    
    return story
```

### Implementation Details

- **Locate the `crawler.py` file**: The Python crawler implementation is located in `src/services/crawler.py`.
- **Update extraction parameters**: Modify `prompt` or `LLMExtractionStrategy` parameters directly in `crawler.py` to fine-tune AI extraction.
- **Adjust concurrency**: Change `settings.max_concurrent` in your config manager (see `utils/crawlerConfig.py`) to control parallelism.
- **Playwright config**: Change browser settings via `BrowserConfig` (e.g. headless, timeout).
- **Post-processing Hooks**: Use `utils/storyProcessor.py` to add custom post-processing functions.

## Performance Optimization

### Memory Management

For large-scale crawling, consider these optimizations:

1. **Limit Concurrent Tasks**: Control the number of browser instances:

```python
# Create a semaphore to limit concurrent tasks
semaphore = asyncio.Semaphore(5)  # Maximum 5 concurrent browser instances

async def bounded_scrape(source):
    async with semaphore:
        return await scrape_website(source["identifier"], current_date)
```

2. **Browser Resource Management**:

```python
# Close browser when done to free resources
async with AsyncWebCrawler(config=browser_cfg) as crawler:
    result = await crawler.arun(url=url, config=run_cfg)
    # Browser automatically closes after block
```

### Caching Strategies

Configure caching for performance and to reduce load on target sites:

```python
# Use in-memory cache for short-term scraping sessions
run_cfg = CrawlerRunConfig(
    cache_mode=CacheMode.USE_CACHE,
    cache_ttl=60 * 60,  # Cache results for 1 hour
)
```

## Advanced Crawl4AI Features

### Following Links with Graph Crawler

For sites where you need to follow links to get complete content:

```python
from crawl4ai import AsyncGraphCrawler

crawler = AsyncGraphCrawler(
    max_depth=2,  # Follow links up to 2 levels deep
    max_pages=10,  # Limit to 10 pages total
    same_domain_only=True  # Stay on the same domain
)
```

### JavaScript Execution

Execute custom JavaScript to interact with pages or extract data:

```python
run_cfg = CrawlerRunConfig(
    js_snippet="""
        // Scroll to bottom of page to load lazy content
        window.scrollTo(0, document.body.scrollHeight);
        // Click "Load More" button if it exists
        const loadMoreBtn = document.querySelector('.load-more');
        if (loadMoreBtn) loadMoreBtn.click();
    """,
    wait_after_js=2000  # Wait 2 seconds after JS execution
)
```

## Troubleshooting Common Issues

### Handling Rate Limiting

If you encounter rate limiting:

```python
# Implement exponential backoff
async def scrape_with_retry(url, retries=3, backoff=2):
    for attempt in range(retries):
        try:
            return await scrape_website(url, current_date)
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                wait_time = backoff ** attempt
                logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
            else:
                raise
```

### Debugging Extraction Issues

To debug extraction problems:

```python
# Add verbose logging
run_cfg = CrawlerRunConfig(
    verbose=True,
    debug_extraction=True  # Save intermediate extraction results
)

# Save raw HTML for inspection
with open("debug_page.html", "w", encoding="utf-8") as f:
    f.write(result.html)
```

### Browser Automation Problems

For issues with Playwright/browser automation:

```bash
# Check browser installation
python -m playwright install chromium
python -m playwright install-deps

# Test browser launch
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop()"
```

## Resources and Further Reading

- [Crawl4AI Documentation](https://docs.crawl4ai.com/)
- [Playwright Documentation](https://playwright.dev/python/docs/intro)
- [Python AsyncIO Guide](https://docs.python.org/3/library/asyncio.html)
