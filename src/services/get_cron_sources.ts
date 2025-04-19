import dotenv from "dotenv";
import fs from "fs";
import path from "path";

dotenv.config();

interface Source {
  identifier: string;
  type: string;
}

interface SourceConfig {
  web_sources: Source[];
  twitter_sources: Source[];
}

export async function getCronSources(): Promise<Source[]> {
  try {
    console.log("Fetching sources from configuration file...");

    // Check for required API keys
    const hasXApiKey = !!process.env.X_API_BEARER_TOKEN;
    const hasFirecrawlKey = !!process.env.FIRECRAWL_API_KEY;

    // Read sources from JSON file
    const sourcesPath = path.join(process.cwd(), "sources.json");
    let sources: Source[] = [];

    try {
      const fileContents = fs.readFileSync(sourcesPath, "utf8");
      const sourceConfig: SourceConfig = JSON.parse(fileContents);
      
      // Filter sources based on available API keys
      if (hasFirecrawlKey) {
        sources = [...sources, ...sourceConfig.web_sources];
      } else {
        console.log("Missing FIRECRAWL_API_KEY - web sources will be skipped");
      }
      
      if (hasXApiKey) {
        sources = [...sources, ...sourceConfig.twitter_sources];
      } else {
        console.log("Missing X_API_BEARER_TOKEN - Twitter sources will be skipped");
      }
    } catch (error) {
      console.error("Error reading sources.json:", error);
      
      // Fallback to hardcoded sources if file not found
      console.log("Using fallback hardcoded sources...");
      
      const fallbackSources: Source[] = [
        ...(hasFirecrawlKey
          ? [
              { identifier: "https://www.firecrawl.dev/blog", type: "website" },
              { identifier: "https://openai.com/news/", type: "website" },
              { identifier: "https://www.anthropic.com/news", type: "website" },
            ]
          : []),
        ...(hasXApiKey ? [{ identifier: "https://x.com/skirano", type: "twitter" }] : []),
      ];
      
      sources = fallbackSources;
    }

    console.log(`Found ${sources.length} sources to monitor`);
    return sources;
  } catch (error) {
    console.error("Error in getCronSources:", error);
    return [];
  }
}
