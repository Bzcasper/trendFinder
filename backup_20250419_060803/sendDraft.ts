import axios from 'axios';
import dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';

dotenv.config();

// Add colors for console output
const colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m"
};

/**
 * Send draft to Discord webhook
 */
async function sendDraftToDiscord(draft_post: string) {
  try {
    console.log(`${colors.cyan}Attempting to send draft to Discord webhook...${colors.reset}`);
    
    const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
    if (!webhookUrl) {
      throw new Error("DISCORD_WEBHOOK_URL not set in environment variables");
    }
    
    const response = await axios.post(
      webhookUrl,
      {
        content: draft_post,
        flags: 4 // SUPPRESS_EMBEDS
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    console.log(`${colors.green}Successfully sent draft to Discord webhook${colors.reset}`);
    // Also save a copy to file as backup
    saveDraftToFile(draft_post, 'discord_success');
    return `Success sending draft to Discord webhook at ${new Date().toISOString()}`;
  } catch (error: any) {
    console.log(`${colors.red}Error sending draft to Discord webhook${colors.reset}`);
    
    if (error.response) {
      console.error(`${colors.red}Response error: ${error.response.status} - ${JSON.stringify(error.response.data)}${colors.reset}`);
    } else if (error.request) {
      console.error(`${colors.red}Request error: No response received${colors.reset}`);
    } else {
      console.error(`${colors.red}Error: ${error.message}${colors.reset}`);
    }
    
    // Save draft to file as backup
    saveDraftToFile(draft_post, 'discord_error');
    throw error;
  }
}

/**
 * Send draft to Slack webhook
 */
async function sendDraftToSlack(draft_post: string) {
  try {
    console.log(`${colors.cyan}Attempting to send draft to Slack webhook...${colors.reset}`);
    
    const webhookUrl = process.env.SLACK_WEBHOOK_URL;
    if (!webhookUrl) {
      throw new Error("SLACK_WEBHOOK_URL not set in environment variables");
    }
    
    const response = await axios.post(
      webhookUrl,
      {
        text: draft_post,
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    console.log(`${colors.green}Successfully sent draft to Slack webhook${colors.reset}`);
    // Also save a copy to file as backup
    saveDraftToFile(draft_post, 'slack_success');
    return `Success sending draft to Slack webhook at ${new Date().toISOString()}`;
  } catch (error: any) {
    console.log(`${colors.red}Error sending draft to Slack webhook${colors.reset}`);
    
    if (error.response) {
      console.error(`${colors.red}Response error: ${error.response.status} - ${JSON.stringify(error.response.data)}${colors.reset}`);
    } else if (error.request) {
      console.error(`${colors.red}Request error: No response received${colors.reset}`);
    } else {
      console.error(`${colors.red}Error: ${error.message}${colors.reset}`);
    }
    
    // Save draft to file as backup
    saveDraftToFile(draft_post, 'slack_error');
    
    // Return error message instead of throwing
    return `Error sending draft to Slack webhook: ${error.message}`;
  }
}

/**
 * Save draft to file (dedicated file driver option)
 */
function sendDraftToFile(draft_post: string) {
  try {
    console.log(`${colors.cyan}Saving draft to file...${colors.reset}`);
    
    const result = saveDraftToFile(draft_post, 'output');
    console.log(`${colors.green}Successfully saved draft to file: ${result}${colors.reset}`);
    return `Success saving draft to file at ${new Date().toISOString()}: ${result}`;
  } catch (error: any) {
    console.error(`${colors.red}Error saving draft to file: ${error.message}${colors.reset}`);
    return `Error saving draft to file: ${error.message}`;
  }
}

/**
 * Save draft to file as backup or primary output
 * Returns the path to the saved file
 */
function saveDraftToFile(draft_post: string, prefix: string): string {
  try {
    // Create backup directory if it doesn't exist
    const outputDir = process.env.OUTPUT_DIR || path.join(process.cwd(), 'output');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Create filename with timestamp
    const timestamp = new Date().toISOString().replace(/:/g, '-');
    const filename = path.join(outputDir, `${prefix}_${timestamp}.txt`);
    
    // Write draft to file
    fs.writeFileSync(filename, draft_post);
    console.log(`${colors.yellow}Draft saved to ${filename}${colors.reset}`);
    
    return filename;
  } catch (error) {
    console.error(`${colors.red}Error saving draft to file: ${error}${colors.reset}`);
    throw error;
  }
}

/**
 * Send draft to configured notification service
 */
export async function sendDraft(draft_post: string) {
  const notificationDriver = process.env.NOTIFICATION_DRIVER?.toLowerCase();
  console.log(`${colors.blue}Using notification driver: ${notificationDriver || 'not set'}${colors.reset}`);

  switch (notificationDriver) {
    case 'slack':
      return sendDraftToSlack(draft_post);
    case 'discord':
      return sendDraftToDiscord(draft_post);
    case 'file':
      return sendDraftToFile(draft_post);
    default:
      const errorMsg = `Unsupported notification driver: ${notificationDriver}`;
      console.error(`${colors.red}${errorMsg}${colors.reset}`);
      
      // Save draft to file as fallback
      saveDraftToFile(draft_post, 'unsupported_driver');
      return `Error: ${errorMsg}`;
  }
}