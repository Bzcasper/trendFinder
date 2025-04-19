import dotenv from "dotenv";
import fs from "fs";
import path from "path";

dotenv.config();

// Colors for console output
const colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m"
};

export interface Source {
  identifier: string;
  type: string;
}

interface SourceConfig {
  web_sources: Source[];
  twitter_sources: Source[];
}

export async function getCronSources(): Promise<Source[]> {
  try {
    console.log(`${colors.cyan}Fetching sources from configuration file...${colors.reset}`);

    // Check for required API keys
    const hasXApiKey = !!process.env.X_API_BEARER_TOKEN;
    const hasFirecrawlKey = !!process.env.FIRECRAWL_API_KEY;
    
    // Use this path for sources file (uses sources_config.json instead of sources.json)
    const sourcesPath = path.join(process.cwd(), 'sources_config.json');
    let sources: Source[] = [];

    try {
      // Check if file exists
      if (!fs.existsSync(sourcesPath)) {
        console.log(`${colors.yellow}Sources file not found at ${sourcesPath}${colors.reset}`);
        // Check the alternative path
        const altPath = path.join(process.cwd(), 'sources.json');
        if (fs.existsSync(altPath) && !fs.lstatSync(altPath).isDirectory()) {
          console.log(`${colors.green}Found alternative sources file at ${altPath}${colors.reset}`);
          const fileContents = fs.readFileSync(altPath, "utf8");
          const sourceConfig: SourceConfig = JSON.parse(fileContents);
          
          // Filter sources based on available API keys
          if (hasFirecrawlKey) {
            sources = [...sources, ...sourceConfig.web_sources];
          } else {
            console.log(`${colors.yellow}Missing FIRECRAWL_API_KEY - web sources will be skipped${colors.reset}`);
          }
          
          if (hasXApiKey) {
            sources = [...sources, ...sourceConfig.twitter_sources];
          } else {
            console.log(`${colors.yellow}Missing X_API_BEARER_TOKEN - Twitter sources will be skipped${colors.reset}`);
          }
          
          return sources;
        }
        
        // If no sources file found, use hardcoded fallback
        return getDefaultSources(hasXApiKey, hasFirecrawlKey);
      }
      
      // Read from sources_config.json
      const fileContents = fs.readFileSync(sourcesPath, "utf8");
      const sourceConfig: SourceConfig = JSON.parse(fileContents);
      
      // Filter sources based on available API keys
      if (hasFirecrawlKey) {
        sources = [...sources, ...sourceConfig.web_sources];
      } else {
        console.log(`${colors.yellow}Missing FIRECRAWL_API_KEY - web sources will be skipped${colors.reset}`);
      }
      
      if (hasXApiKey) {
        sources = [...sources, ...sourceConfig.twitter_sources];
      } else {
        console.log(`${colors.yellow}Missing X_API_BEARER_TOKEN - Twitter sources will be skipped${colors.reset}`);
      }
    } catch (error) {
      console.error(`${colors.red}Error reading sources file: ${error}${colors.reset}`);
      
      // Fallback to hardcoded sources
      return getDefaultSources(hasXApiKey, hasFirecrawlKey);
    }

    console.log(`${colors.green}Found ${sources.length} sources to monitor${colors.reset}`);
    return sources;
  } catch (error) {
    console.error(`${colors.red}Error in getCronSources: ${error}${colors.reset}`);
    return [];
  }
}

/**
 * Get default hardcoded sources if no sources file is found
 */
function getDefaultSources(hasXApiKey: boolean, hasFirecrawlKey: boolean): Source[] {
  console.log(`${colors.yellow}Using fallback hardcoded sources...${colors.reset}`);
  
  const fallbackSources: Source[] = [
    ...(hasFirecrawlKey
      ? [
          { identifier: "https://modal.com/docs", type: "website" },
          { identifier: "https://openai.com/news/", type: "website" },
          { identifier: "https://www.anthropic.com/news", type: "website" },
        ]
      : []),
    ...(hasXApiKey ? [{ identifier: "https://x.com/skirano", type: "twitter" }] : []),
  ];
  
  return fallbackSources;
}