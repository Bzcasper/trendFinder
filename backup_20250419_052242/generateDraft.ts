import axios from "axios";
import dotenv from "dotenv";
import * as fs from "fs";
import * as path from "path";

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
 * Save raw content to file for debugging
 */
function saveToDebugFile(content: string, prefix: string): void {
  try {
    // Create debug directory if it doesn't exist
    const debugDir = path.join(process.cwd(), 'debug');
    if (!fs.existsSync(debugDir)) {
      fs.mkdirSync(debugDir, { recursive: true });
    }
    
    // Create filename with timestamp
    const timestamp = new Date().toISOString().replace(/:/g, '-');
    const filename = path.join(debugDir, `${prefix}_${timestamp}.json`);
    
    // Write content to file
    fs.writeFileSync(filename, content);
    console.log(`${colors.blue}Debug content saved to ${filename}${colors.reset}`);
  } catch (error) {
    console.error(`${colors.red}Error saving debug file: ${error}${colors.reset}`);
  }
}

/**
 * Generate a post draft based on scraped raw stories using our Modal-hosted API.
 * If no items are found, a fallback message is returned.
 */
export async function generateDraft(rawStories: string) {
  console.log(
    `${colors.cyan}Generating a post draft with raw stories (${rawStories.length} characters)...${colors.reset}`,
  );

  try {
    const currentDate = new Date().toLocaleDateString();
    const header = `🚀 AI and LLM Trends for ${currentDate}\n\n`;

    // Save raw stories for debugging
    saveToDebugFile(rawStories, "raw_stories");

    // Try multiple API endpoints in order of preference
    const apiEndpoints = [
      {
        name: "Modal API",
        url: process.env.MODAL_API_URL,
        token: process.env.MODAL_API_TOKEN,
        type: "modal"
      },
      {
        name: "DeepSeek API",
        url: "https://api.deepseek.com/v1/chat/completions",
        token: process.env.DEEPSEEK_API_KEY,
        type: "openai"
      }
    ];

    // If no stories found or empty content
    if (!rawStories || rawStories.length < 10) {
      console.warn(`${colors.yellow}Warning: No or very little raw story content${colors.reset}`);
      return header + "No trending stories or tweets found at this time.";
    }

    // Try each API endpoint in order
    for (const api of apiEndpoints) {
      if (!api.url || !api.token) {
        console.log(`${colors.yellow}Skipping ${api.name} - missing URL or token${colors.reset}`);
        continue;
      }

      console.log(`${colors.cyan}Trying ${api.name} at ${api.url}${colors.reset}`);

      try {
        // Create a request to our API
        const apiClient = axios.create({
          baseURL: api.url,
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${api.token}`
          }
        });

        // Prepare system message for structured output
        const systemMessage = `You are a helpful assistant that creates a concise, bullet-pointed draft post based on input stories and tweets. 
          Return strictly valid JSON that has a key 'interestingTweetsOrStories' containing an array of items. 
          Each item should have a 'description' and a 'story_or_tweet_link' key.`;

        // Call the API (which follows OpenAI-compatible format)
        const response = await apiClient.post("/v1/chat/completions", {
          model: api.type === "modal" ? "mistral-7b-instruct" : "deepseek-chat",
          messages: [
            { role: "system", content: systemMessage },
            { role: "user", content: rawStories }
          ],
          temperature: 0.3, // Lower temperature for more consistent, structured output
          max_tokens: 1024
        });

        // Extract the response content
        const rawJSON = api.type === "modal" 
          ? response.data.choices[0].message.content 
          : response.data.choices[0].message.content;

        if (!rawJSON) {
          console.log(`${colors.yellow}No JSON output returned from ${api.name}.${colors.reset}`);
          continue; // Try next API
        }

        // Save API response for debugging
        saveToDebugFile(JSON.stringify(response.data), `${api.name.toLowerCase()}_response`);

        try {
          const parsedResponse = JSON.parse(rawJSON);
          console.log(`${colors.green}Successfully parsed response from ${api.name}${colors.reset}`);

          // Check for either key and see if we have any content
          const contentArray =
            parsedResponse.interestingTweetsOrStories || parsedResponse.stories || [];
          if (contentArray.length === 0) {
            console.log(`${colors.yellow}No content items found in the parsed response${colors.reset}`);
            return header + "No trending stories or tweets found at this time.";
          }

          // Build the draft post using the content array
          const draft_post =
            header +
            contentArray
              .map(
                (item: any) =>
                  `• ${item.description || item.headline}\n  ${
                    item.story_or_tweet_link || item.link
                  }`,
              )
              .join("\n\n");

          console.log(`${colors.green}Successfully generated draft with ${contentArray.length} items${colors.reset}`);
          return draft_post;
        } catch (parseError) {
          console.error(`${colors.red}Error parsing API response as JSON from ${api.name}:${colors.reset}`, parseError);
          saveToDebugFile(rawJSON, "failed_parse");
          
          // Continue to next API if available
          continue;
        }
      } catch (apiError: any) {
        console.error(`${colors.red}Error with ${api.name}:${colors.reset}`, apiError?.message || apiError);
        
        // Log detailed error for debugging
        if (apiError.response) {
          console.error(`${colors.red}API error details:${colors.reset}`, {
            status: apiError.response.status,
            data: apiError.response.data
          });
        }
        
        // Continue to next API
        continue;
      }
    }
    
    // If we get here, all APIs failed
    console.error(`${colors.red}All API endpoints failed. Generating fallback response.${colors.reset}`);
    
    // Create simple fallback response
    return header + "Unable to generate trends at this time. Please check your API configuration and try again later.";

  } catch (error: any) {
    console.error(`${colors.red}Error generating draft post:${colors.reset}`, error?.message || error);
    
    // Provide detailed error information for debugging
    if (error.response) {
      console.error(`${colors.red}API error details:${colors.reset}`, {
        status: error.response.status,
        data: error.response.data
      });
    }
    
    return "Error generating draft post. Please check logs for details.";
  }
}