import { handleCron } from "./controllers/cron";
import cron from 'node-cron';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

// Colors for console output
const colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
  bright: "\x1b[1m"
};

// Configure environment variables
dotenv.config();

// Ensure output directory exists
const outputDir = process.env.OUTPUT_DIR || './output';
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Main execution function
async function main() {
  try {
    console.log(`${colors.bright}${colors.cyan}✨ Trend Finder Starting...${colors.reset}`);
    console.log(`${colors.blue}🔍 Starting process to generate draft...${colors.reset}`);
    
    // Log timestamp
    const startTime = new Date();
    console.log(`${colors.yellow}⏱️  Start time: ${startTime.toLocaleString()}${colors.reset}`);
    
    // Execute the cron handler
    await handleCron();
    
    // Calculate duration
    const endTime = new Date();
    const duration = (endTime.getTime() - startTime.getTime()) / 1000;
    
    console.log(`${colors.green}✅ Process completed successfully in ${duration.toFixed(2)} seconds${colors.reset}`);
  } catch (error) {
    console.error(`${colors.red}❌ Process failed with error: ${error}${colors.reset}`);
    
    // Log error to file for debugging
    const errorLog = path.join(outputDir, `error_log_${new Date().toISOString().replace(/:/g, '-')}.txt`);
    fs.writeFileSync(errorLog, `Error at ${new Date().toISOString()}\n${error}\n${error.stack || 'No stack trace'}`);
    
    console.log(`${colors.yellow}📝 Error details saved to ${errorLog}${colors.reset}`);
  }
}

// Execute main function immediately
main();

// For scheduled execution (commented out by default)
// This will run the task at 5 PM every day
// Uncomment the following section to enable scheduled execution:

/*
cron.schedule(`0 17 * * *`, async () => {
  console.log(`${colors.blue}⏰ Scheduled task starting at ${new Date().toLocaleString()}${colors.reset}`);
  await main();
});

console.log(`${colors.yellow}🕒 Cron job scheduled to run at 5:00 PM daily${colors.reset}`);
*/