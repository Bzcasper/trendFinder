#!/usr/bin/env node

/**
 * Script to create a valid sources.json file
 * Run with: node create_sources_json.js
 */

const fs = require('fs');
const path = require('path');
const process = require('process');

// Default content for sources.json
const defaultSources = {
  web_sources: [
    { identifier: "https://modal.com/docs", type: "website" },
    { identifier: "https://openai.com/blog", type: "website" },
    { identifier: "https://www.anthropic.com/news", type: "website" }
  ],
  twitter_sources: [
    { identifier: "https://x.com/skirano", type: "twitter" }
  ]
};

// Path for the new sources.json
const sourcesPath = path.join(process.cwd(), 'sources_config.json');

try {
  // Check if there's a directory with the same name
  const dirPath = path.join(process.cwd(), 'sources.json');
  if (fs.existsSync(dirPath) && fs.lstatSync(dirPath).isDirectory()) {
    console.log('\x1b[33m%s\x1b[0m', `Warning: sources.json exists as a directory. Using ${sourcesPath} instead.`);
  }

  // Save the default sources to the file
  const jsonString = JSON.stringify(defaultSources, null, 2);
  fs.writeFileSync(sourcesPath, jsonString);
  
  console.log('\x1b[32m%s\x1b[0m', `Created ${sourcesPath} successfully!`);
  console.log('\x1b[36m%s\x1b[0m', 'Content:');
  console.log(jsonString);
  
  // Create a symbolic link if possible (Windows might need admin privileges)
  try {
    if (fs.existsSync(dirPath) && fs.lstatSync(dirPath).isDirectory()) {
      console.log('\x1b[33m%s\x1b[0m', `Cannot create symlink: sources.json is a directory`);
    } else if (fs.existsSync(dirPath)) {
      console.log('\x1b[33m%s\x1b[0m', `Cannot create symlink: sources.json already exists as a file`);
    } else {
      // This might fail on Windows without admin privileges
      fs.symlinkSync(sourcesPath, path.join(process.cwd(), 'sources.json'));
      console.log('\x1b[32m%s\x1b[0m', `Created symlink from sources.json to ${sourcesPath}`);
    }
  } catch (linkError) {
    console.log('\x1b[33m%s\x1b[0m', `Could not create symlink (may need admin privileges): ${linkError.message}`);
  }
  
  // Now update the getCronSources.ts to use the new file
  console.log('\x1b[36m%s\x1b[0m', '\nTo use this file, update your getCronSources.ts file to use this path:');
  console.log(`\`const sourcesPath = path.join(process.cwd(), 'sources_config.json');\``);
  
} catch (error) {
  console.error('\x1b[31m%s\x1b[0m', `Error creating sources.json: ${error.message}`);
  process.exit(1);
}
