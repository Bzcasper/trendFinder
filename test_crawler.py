#!/usr/bin/env python
"""
Simple test script for the crawler
"""

import sys
import json
import subprocess
import os

# Test sources
test_sources = [
    {"identifier": "https://example.com", "type": "website"}
]

# Convert to JSON string
sources_json = json.dumps(test_sources)

# Path to crawler script
crawler_path = os.path.join("src", "services", "crawler.py")

print(f"Testing crawler with: {sources_json}")

# Run the crawler with this input
try:
    # Use single quotes for the JSON string on Windows
    cmd = f"python {crawler_path} '{sources_json}'"
    print(f"Executing: {cmd}")
    
    result = subprocess.run(
        cmd,
        shell=True,
        check=True,
        capture_output=True,
        text=True
    )
    
    print("\nOutput:")
    print(result.stdout)
    
    if result.stderr:
        print("\nErrors:")
        print(result.stderr)
    
    # Parse JSON output
    try:
        output = json.loads(result.stdout)
        print("\nParsed JSON output:")
        print(f"Stories found: {len(output.get('stories', []))}")
        print(f"Errors: {len(output.get('errors', []))}")
    except json.JSONDecodeError:
        print("\nCouldn't parse JSON output")
        
except subprocess.CalledProcessError as e:
    print(f"\nError executing crawler: {e}")
    print(f"Exit code: {e.returncode}")
    if e.stdout:
        print(f"Output: {e.stdout}")
    if e.stderr:
        print(f"Error output: {e.stderr}")
    
except Exception as e:
    print(f"\nUnexpected error: {e}")
