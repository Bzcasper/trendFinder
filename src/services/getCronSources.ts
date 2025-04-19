import dotenv from "dotenv";
import process from 'process';

dotenv.config();

export async function getCronSources(): Promise<{ identifier: string; type: string }[]> {
  try {
    console.log("Fetching sources...");

    // Check for required API keys
    const hasXApiKey = !!process.env.X_API_BEARER_TOKEN;
    const hasFirecrawlKey = !!process.env.FIRECRAWL_API_KEY;

    // Define sources based on available API keys
    const sources: { identifier: string; type: string }[] = [
      ...(hasFirecrawlKey
        ? [
            { identifier: "https://www.firecrawl.dev/blog", type: "website" },
            { identifier: "https://openai.com/news/", type: "website" },
            { identifier: "https://www.anthropic.com/news", type: "website" },
            { identifier: "https://news.ycombinator.com/", type: "website" },
            { identifier: "https://www.reuters.com/technology/artificial-intelligence/", type: "website" },
            { identifier: "https://simonwillison.net/", type: "website" },
            { identifier: "https://buttondown.com/ainews/archive/", type: "website" },
          ]
        : []),
      ...(hasXApiKey ? [{ identifier: "https://x.com/skirano", type: "twitter" }] : []),
    ];

    // Return the full objects instead of mapping to strings
    return sources;
  } catch (error) {
    console.error(error);
    return [];
  }
}
