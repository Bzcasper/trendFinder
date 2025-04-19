# Trend Finder 🔦

**Stay on top of trending topics in AI and LLMs — all in one place.**

Trend Finder collects and analyzes posts from key influencers and websites, then sends a Slack or Discord notification when it detects new trends or product launches. This has been a complete game-changer for staying informed by:

- **Saving time** normally spent manually searching social channels
- **Keeping you informed** of relevant, real-time conversations
- **Enabling rapid response** to new opportunities or emerging industry shifts

_Spend less time hunting for trends and more time creating impactful campaigns._

## How it Works

1. **Data Collection** 📥
   - Monitors selected Twitter/X accounts using the X API
   - Monitors websites for new releases and news with Python-based Crawl4AI
   - Uses a customizable sources.json configuration file
   - Runs on a scheduled basis using cron jobs

2. **AI Analysis** 🧠
   - Processes collected content through a custom Modal-hosted API
   - Uses an open-source Mistral-7B model to analyze and summarize content
   - Identifies emerging trends, releases, and news
   - Formats findings into a structured, readable format

3. **Notification System** 📢
   - When significant trends are detected, sends Slack or Discord notifications
   - Provides context about the trend and its sources
   - Enables quick response to emerging opportunities

## Features

- 🤖 AI-powered trend analysis using your own hosted Modal API
- 📱 Social media monitoring (Twitter/X integration)
- 🔍 Website monitoring with Python-based Crawl4AI
- 💬 Instant Slack or Discord notifications
- ⏱️ Scheduled monitoring using cron jobs
- 🔧 Customizable sources via JSON configuration

## Prerequisites

- Node.js (v14 or higher)
- Python 3.9+ with pip
- npm or yarn
- Modal account for hosting the AI model API
- X/Twitter API access (optional, for monitoring Twitter accounts)

## Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

```
# Modal API configuration
MODAL_API_URL=https://your-modal-app-endpoint.modal.run
MODAL_API_TOKEN=your-modal-api-token-here

# Required if monitoring Twitter/X trends (https://developer.x.com/)
X_API_BEARER_TOKEN=your_twitter_api_bearer_token_here

# Notification driver. Supported drivers: "slack", "discord"
NOTIFICATION_DRIVER=discord

# Required (if NOTIFICATION_DRIVER is "slack"): Incoming Webhook URL from Slack for notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Required (if NOTIFICATION_DRIVER is "discord"): Incoming Webhook URL from Discord for notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/WEBHOOK/URL
```

## Modal Setup

1. **Install Modal CLI**:
   ```bash
   pip install modal
   ```

2. **Deploy the Modal API Server**:
   ```bash
   modal deploy modal_server.py
   ```

3. **Get your Modal API URL**:
   Once deployed, Modal will provide a URL for your API endpoint. Update your `.env` file with this URL.

## Customizing Sources

Edit the `sources.json` file to customize which websites and Twitter accounts are monitored:

```json
{
  "web_sources": [
    {"identifier": "https://openai.com/news/", "type": "website"}
  ],
  "twitter_sources": [
    {"identifier": "https://x.com/OpenAI", "type": "twitter"}
  ]
}
```

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone [repository-url]
   cd trend-finder
   ```

2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   
   This will:
   - Create a Python virtual environment
   - Install Crawl4AI and its dependencies
   - Install Playwright browsers
   - Install Node.js dependencies
   - Create a .env file from the template

3. **Configure environment variables:**
   ```bash
   # Edit .env with your configuration
   nano .env
   ```

4. **Deploy your Modal API:**
   ```bash
   modal deploy modal_server.py
   ```

5. **Run the application:**
   ```bash
   # Make sure the Python virtual environment is activated
   source venv/bin/activate
   
   # Start the application
   npm start
   ```

## How Crawl4AI Works

This application uses Crawl4AI, a powerful Python-based web crawler specially designed for AI applications. Some key features:

1. **Browser Automation**: Uses Playwright to control real browsers, enabling extraction from JavaScript-heavy sites.

2. **Asynchronous Processing**: Efficiently crawls multiple sites in parallel.

3. **AI-Powered Extraction**: Automatically extracts structured data using models like Mistral.

4. **Clean Markdown Generation**: Converts web content to clean, LLM-friendly markdown.

The Python scraper service integrates with our TypeScript application, allowing for efficient scraping while leveraging Python's robust AI ecosystem.

## Running as a Scheduled Job

To run the trend finder on a schedule, uncomment the cron configuration in `src/index.ts`:

```typescript
// If you want to run the cron job automatically, uncomment the following line:
cron.schedule(`0 17 * * *`, async () => {
  console.log(`Starting process to generate draft...`);
  await handleCron();
});
```

This will run the process daily at 5 PM server time.

## Project Structure

```
trend-finder/
├── modal_server.py         # Modal API server for inference
├── sources.json            # Configurable sources for monitoring
├── src/
│   ├── controllers/        # Request handlers
│   ├── services/
│   │   ├── crawler.py      # Python-based Crawl4AI scraper
│   │   ├── getCronSources.ts  # Source configuration manager
│   │   ├── generateDraft.ts   # Draft generation using Modal API
│   │   ├── scrapeSources.ts   # TypeScript interface to Python crawler
│   │   └── sendDraft.ts       # Notification sender
│   └── index.ts            # Application entry point
├── .env.example            # Environment variables template
├── setup.sh               # Setup script for dependencies
├── package.json            # Dependencies and scripts
└── tsconfig.json           # TypeScript configuration
```

## Troubleshooting

### Crawl4AI Issues

If you encounter issues with the Crawl4AI integration:

1. **Check Python Environment**: Make sure your virtual environment is activated and Crawl4AI is installed:
   ```bash
   source venv/bin/activate
   pip install -U crawl4ai
   ```

2. **Run Crawl4AI Doctor**: Diagnose potential issues with browsers:
   ```bash
   python -c "from crawl4ai.doctor import run_doctor_checks; run_doctor_checks()"
   ```

3. **Verify Playwright**: Make sure browsers are installed:
   ```bash
   python -m playwright install
   ```

4. **Test the Crawler Directly**: You can test the Python crawler directly:
   ```bash
   python src/services/crawler.py '[{"identifier": "https://example.com", "type": "website"}]'
   ```

### Twitter API Issues

For Twitter/X API issues:

1. **Check Bearer Token**: Ensure your X_API_BEARER_TOKEN is correctly configured in the .env file.

2. **API Limits**: Note that the Twitter v2 API has rate limits. If you hit them, some sources may be skipped.

### Modal API Issues

For Modal API issues:

1. **Check Connection**: Verify that your MODAL_API_URL and MODAL_API_TOKEN are correct.

2. **Check Logs**: Check the Modal dashboard for any errors in your deployment.

3. **Redeployment**: Try redeploying your Model API: `modal deploy modal_server.py`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Crawl4AI](https://github.com/unclecode/crawl4ai) - The powerful Python web crawler used in this project
- [Modal](https://modal.com) - For hosting our inference API
- [Node.js](https://nodejs.org/) and [TypeScript](https://www.typescriptlang.org/) - Core technologies