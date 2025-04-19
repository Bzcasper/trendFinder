import axios from "axios";
import dotenv from "dotenv";

dotenv.config();

/**
 * Generate a post draft based on scraped raw stories using our Modal-hosted API.
 * If no items are found, a fallback message is returned.
 */
export async function generateDraft(rawStories: string) {
  console.log(
    `Generating a post draft with raw stories (${rawStories.length} characters)...`,
  );

  try {
    const currentDate = new Date().toLocaleDateString();
    const header = `🚀 AI and LLM Trends for ${currentDate}\n\n`;

    // Use our custom Modal API endpoint
    const modalApiUrl = process.env.MODAL_API_URL;
    const modalApiToken = process.env.MODAL_API_TOKEN;

    if (!modalApiUrl || !modalApiToken) {
      throw new Error("MODAL_API_URL and MODAL_API_TOKEN environment variables must be set");
    }

    // Create a request to our API
    const apiClient = axios.create({
      baseURL: modalApiUrl,
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${modalApiToken}`
      }
    });

    // Prepare system message for structured output
    const systemMessage = `You are a helpful assistant that creates a concise, bullet-pointed draft post based on input stories and tweets. 
      Return strictly valid JSON that has a key 'interestingTweetsOrStories' containing an array of items. 
      Each item should have a 'description' and a 'story_or_tweet_link' key.`;

    // Call the Modal API (which follows OpenAI-compatible format)
    const response = await apiClient.post("/v1/chat/completions", {
      model: "mistral-7b-instruct",
      messages: [
        { role: "system", content: systemMessage },
        { role: "user", content: rawStories }
      ],
      temperature: 0.3, // Lower temperature for more consistent, structured output
      max_tokens: 1024
    });

    // Extract the response content
    const rawJSON = response.data.choices[0].message.content;
    if (!rawJSON) {
      console.log("No JSON output returned from API.");
      return header + "No output.";
    }
    console.log(rawJSON);

    try {
      const parsedResponse = JSON.parse(rawJSON);

      // Check for either key and see if we have any content
      const contentArray =
        parsedResponse.interestingTweetsOrStories || parsedResponse.stories || [];
      if (contentArray.length === 0) {
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

      return draft_post;
    } catch (parseError) {
      console.error("Error parsing API response as JSON:", parseError);
      
      // Fallback: if response isn't valid JSON, use the raw text with some formatting
      return header + "Failed to parse structured output. Raw model output:\n\n" + rawJSON;
    }
  } catch (error: any) {
    console.error("Error generating draft post:", error?.message || error);
    
    // Provide detailed error information for debugging
    if (error.response) {
      console.error("API error details:", {
        status: error.response.status,
        data: error.response.data
      });
    }
    
    return "Error generating draft post. Please check logs for details.";
  }
}
