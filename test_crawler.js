#!/usr/bin/env node

/**
 * Test script for the Python Crawl4AI scraper
 * Run with: node test_crawler.js
 */

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

// Path to the Python crawler script
const crawlerPath = path.join(__dirname, 'src', 'services', 'crawler.py');

// Test sources - modify as needed
const testSources = [
  { identifier: 'https://example.com', type: 'website' },
  // Add more test sources as needed
];

// Convert sources to JSON string for passing to Python
const sourcesJson = JSON.stringify(testSources);

console.log('Testing Python Crawl4AI crawler...');
console.log(`Sources: ${sourcesJson}`);

// Run the Python crawler with our test sources
exec(`python ${crawlerPath} '${sourcesJson}'`, (error, stdout, stderr) => {
  if (error) {
    console.error(`Error executing crawler: ${error.message}`);
    return;
  }
  
  if (stderr) {
    console.error(`Crawler stderr: ${stderr}`);
  }
  
  // Process the stdout as JSON
  try {
    const result = JSON.parse(stdout);
    
    console.log('\n--- Test Results ---');
    console.log(`Total stories found: ${result.stories?.length || 0}`);
    
    if (result.errors && result.errors.length > 0) {
      console.log('\nErrors encountered:');
      result.errors.forEach(error => {
        console.log(`- ${error.source}: ${error.error}`);
      });
    }
    
    if (result.stories && result.stories.length > 0) {
      console.log('\nSample stories:');
      result.stories.slice(0, 3).forEach((story, index) => {
        console.log(`\n${index + 1}. ${story.headline}`);
        console.log(`   Link: ${story.link}`);
        console.log(`   Date: ${story.date_posted}`);
      });
      
      // Save full results to a file for inspection
      fs.writeFileSync(
        'crawler_test_results.json', 
        JSON.stringify(result, null, 2),
        'utf8'
      );
      console.log('\nFull results saved to crawler_test_results.json');
    } else {
      console.log('\nNo stories found in test sources.');
    }
    
  } catch (parseError) {
    console.error('Error parsing crawler output:');
    console.error(parseError);
    console.log('\nRaw output:');
    console.log(stdout);
  }
});
