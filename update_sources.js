#!/usr/bin/env node

/**
 * Helper script to easily manage sources.json
 * Run with: node update_sources.js add website https://example.com
 * or: node update_sources.js add twitter https://x.com/username
 * or: node update_sources.js remove website https://example.com
 * or: node update_sources.js list
 */

const fs = require('fs');
const path = require('path');

// Default sources if file doesn't exist
const defaultSources = {
  web_sources: [],
  twitter_sources: []
};

// Path to sources.json
const sourcesPath = path.join(process.cwd(), 'sources.json');

// Helper to read the current sources
function readSources() {
  try {
    const data = fs.readFileSync(sourcesPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.log('No existing sources.json found, creating a new one.');
    return defaultSources;
  }
}

// Helper to write sources to file
function writeSources(sources) {
  const jsonString = JSON.stringify(sources, null, 2);
  fs.writeFileSync(sourcesPath, jsonString);
  console.log('sources.json updated successfully!');
}

// Helper to list all sources
function listSources(sources) {
  console.log('\n===== SOURCES =====');
  
  console.log('\nWebsites:');
  if (sources.web_sources.length === 0) {
    console.log('  No websites configured');
  } else {
    sources.web_sources.forEach((source, index) => {
      console.log(`  ${index + 1}. ${source.identifier}`);
    });
  }
  
  console.log('\nTwitter:');
  if (sources.twitter_sources.length === 0) {
    console.log('  No Twitter accounts configured');
  } else {
    sources.twitter_sources.forEach((source, index) => {
      console.log(`  ${index + 1}. ${source.identifier}`);
    });
  }
  
  console.log('\n');
}

// Main function
function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  // Read current sources
  const sources = readSources();
  
  // Process commands
  switch (command) {
    case 'add':
      const addType = args[1];
      const addUrl = args[2];
      
      if (!addType || !addUrl) {
        console.error('Usage: node update_sources.js add [website|twitter] URL');
        process.exit(1);
      }
      
      if (addType === 'website') {
        // Check if already exists
        const existingWeb = sources.web_sources.find(s => s.identifier === addUrl);
        if (existingWeb) {
          console.log(`Website ${addUrl} already exists in sources.`);
        } else {
          sources.web_sources.push({ identifier: addUrl, type: 'website' });
          writeSources(sources);
          console.log(`Added website: ${addUrl}`);
        }
      } else if (addType === 'twitter') {
        // Check if already exists
        const existingTwitter = sources.twitter_sources.find(s => s.identifier === addUrl);
        if (existingTwitter) {
          console.log(`Twitter account ${addUrl} already exists in sources.`);
        } else {
          sources.twitter_sources.push({ identifier: addUrl, type: 'twitter' });
          writeSources(sources);
          console.log(`Added Twitter account: ${addUrl}`);
        }
      } else {
        console.error('Type must be "website" or "twitter"');
        process.exit(1);
      }
      break;
      
    case 'remove':
      const removeType = args[1];
      const removeUrl = args[2];
      
      if (!removeType || !removeUrl) {
        console.error('Usage: node update_sources.js remove [website|twitter] URL');
        process.exit(1);
      }
      
      if (removeType === 'website') {
        const initialLength = sources.web_sources.length;
        sources.web_sources = sources.web_sources.filter(s => s.identifier !== removeUrl);
        
        if (sources.web_sources.length < initialLength) {
          writeSources(sources);
          console.log(`Removed website: ${removeUrl}`);
        } else {
          console.log(`Website ${removeUrl} not found in sources.`);
        }
      } else if (removeType === 'twitter') {
        const initialLength = sources.twitter_sources.length;
        sources.twitter_sources = sources.twitter_sources.filter(s => s.identifier !== removeUrl);
        
        if (sources.twitter_sources.length < initialLength) {
          writeSources(sources);
          console.log(`Removed Twitter account: ${removeUrl}`);
        } else {
          console.log(`Twitter account ${removeUrl} not found in sources.`);
        }
      } else {
        console.error('Type must be "website" or "twitter"');
        process.exit(1);
      }
      break;
      
    case 'list':
      listSources(sources);
      break;
      
    default:
      console.log('Available commands:');
      console.log('  node update_sources.js add website https://example.com');
      console.log('  node update_sources.js add twitter https://x.com/username');
      console.log('  node update_sources.js remove website https://example.com');
      console.log('  node update_sources.js remove twitter https://x.com/username');
      console.log('  node update_sources.js list');
      break;
  }
}

// Run the main function
main();
