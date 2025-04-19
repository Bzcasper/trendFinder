import dotenv from "dotenv";
import { exec } from "child_process";
import { promisify } from "util";
import { z } from "zod";
import path from "path";
import fs from "fs";

dotenv.config();

// Convert exec to Promise-based
const execPromise = promisify(exec);

// 1. Define the schema for our expected JSON
const StorySchema = z.object({
  headline: z.string().describe("Story or post headline"),
  link: z.string().describe("A link to the post or story"),
  date_posted: z.string().describe("The date the story or post was published"),
  source_type: z.string().optional().describe("Type of source (website or twitter)"),
  source_domain: z.string().optional().describe("Domain of the source website"),
  source_url: z.string().optional().describe("Original source URL")
});

const ErrorSchema = z.object({
  source: z.string().describe("Source URL that had an error"),
  error: z.string().describe("Error message")
});

const StoriesResponseSchema = z.object({
  stories: z
    .array(StorySchema)
    .describe("A list of today's AI or LLM-related stories"),
  errors: z
    .array(ErrorSchema)
    .optional()
    .describe("List of errors encountered during scraping")
});

// Define the TypeScript type for a story using the schema
type Story = z.infer<typeof StorySchema>;
type ScrapeError = z.infer<typeof ErrorSchema>;
type StoriesResponse = z.infer<typeof StoriesResponseSchema>;

// Define source interface from getCronSources
interface Source {
  identifier: string;
  type: string;
}

/**
 * Logs scrape stats to a JSON file for tracking
 */
function logScrapeStats(startTime: number, stories: Story[], errors: ScrapeError[]) {
  try {
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    const stats = {
      timestamp: new Date().toISOString(),
      duration_ms: duration,
      stories_count: stories.length,
      errors_count: errors.length,
      sources_by_type: {
        website: stories.filter(s => s.source_type === "website").length,
        twitter: stories.filter(s => s.source_type === "twitter").length
      }
    };
    
    // Create stats directory if it doesn't exist
    const statsDir = path.join(process.cwd(), "stats");
    if (!fs.existsSync(statsDir)) {
      fs.mkdirSync(statsDir, { recursive: true });
    }
    
    // Write stats to file
    const statsFile = path.join(statsDir, `scrape_stats_${new Date().toISOString().replace(/:/g, "-")}.json`);
    fs.writeFileSync(statsFile, JSON.stringify(stats, null, 2));
    
    console.log(`Scrape stats logged to ${statsFile}`);
  } catch (error) {
    console.error("Error logging scrape stats:", error);
  }
}

/**
 * Scrape sources using our Python Crawl4AI implementation.
 * This replaces the previous Firecrawl implementation.
 * Returns a combined array of story objects.
 */
export async function scrapeSources(sources: Source[]): Promise<Story[]> {
  const startTime = Date.now();
  
  try {
    console.log(`Starting scrape process for ${sources.length} sources...`);
    
    // Filter out sources without required API keys
    const hasXApiKey = !!process.env.X_API_BEARER_TOKEN;
    
    // If no Twitter API key, filter out Twitter sources
    const filteredSources = sources.filter(source => {
      if (source.type === "twitter" && !hasXApiKey) {
        console.log(`Skipping Twitter source ${source.identifier} - No X_API_BEARER_TOKEN provided`);
        return false;
      }
      return true;
    });
    
    if (filteredSources.length === 0) {
      console.log("No valid sources to scrape after filtering");
      return [];
    }
    
    // Convert sources to JSON string for passing to Python
    const sourcesJson = JSON.stringify(filteredSources);
    
    // Path to the Python crawler script
    const crawlerPath = path.join(__dirname, "crawler.py");
    
    // Set environment variables for the Python script
    const env = {
      ...process.env,
      // Pass any additional environment variables here if needed
      NODE_ENV: process.env.NODE_ENV || 'development'
    };
    
    // Run the Python crawler with our sources
    console.log("Executing Python crawler...");
    console.time("Crawler execution time");
    
    const { stdout, stderr } = await execPromise(`python ${crawlerPath} '${sourcesJson}'`, { env });
    
    console.timeEnd("Crawler execution time");
    
    if (stderr) {
      console.error("Error from Python crawler:", stderr);
    }
    
    // Parse the JSON result from Python
    const result: StoriesResponse = JSON.parse(stdout);
    
    // Log any errors from the Python scraper
    if (result.errors && result.errors.length > 0) {
      console.error(`Errors during scraping (${result.errors.length}):`);
      result.errors.forEach(error => {
        console.error(`- ${error.source}: ${error.error}`);
      });
    }
    
    // Validate the stories against our schema
    const parsedResult = StoriesResponseSchema.parse(result);
    
    // Log stats
    logScrapeStats(startTime, parsedResult.stories, parsedResult.errors || []);
    
    console.log(`Successfully scraped ${parsedResult.stories.length} stories`);
    return parsedResult.stories;
  } catch (error) {
    console.error("Error in scrapeSources:", error);
    // Return empty array on error
    return [];
  }
}

/**
 * Get stats from the last scraping run
 */
export function getLastScrapeStats() {
  try {
    const statsDir = path.join(process.cwd(), "stats");
    if (!fs.existsSync(statsDir)) {
      return null;
    }
    
    // Get all stats files
    const files = fs.readdirSync(statsDir)
      .filter(file => file.startsWith("scrape_stats_"))
      .map(file => path.join(statsDir, file));
    
    if (files.length === 0) {
      return null;
    }
    
    // Sort by modification time (newest first)
    files.sort((a, b) => fs.statSync(b).mtime.getTime() - fs.statSync(a).mtime.getTime());
    
    // Read the latest stats file
    const latestStats = JSON.parse(fs.readFileSync(files[0], 'utf8'));
    return latestStats;
  } catch (error) {
    console.error("Error getting last scrape stats:", error);
    return null;
  }
}
