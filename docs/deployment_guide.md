# Deployment Guide for Trend Finder

This guide covers deploying the Trend Finder application in various environments, from local development to production.

## Prerequisites

- Node.js 16+ and npm
- Python 3.9+ with pip
- Docker and Docker Compose (for containerized deployment)
- API keys for Twitter/X (optional)
- Slack or Discord webhook URL for notifications

## Local Development Setup

### 1. Clone and Setup the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/trend-finder.git
cd trend-finder

# Run the setup script to install dependencies
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Create a Python virtual environment
- Install Crawl4AI and its dependencies
- Install Playwright browsers
- Install Node.js dependencies
- Create a .env file from the template

### 2. Configure Environment Variables

Edit the `.env` file with your specific configuration:

```
# Modal API configuration
MODAL_API_URL=https://your-modal-app-endpoint.modal.run
MODAL_API_TOKEN=your-modal-api-token-here

# Required if monitoring Twitter/X trends
X_API_BEARER_TOKEN=your_twitter_api_bearer_token_here

# Notification driver (slack or discord)
NOTIFICATION_DRIVER=discord

# Webhook URLs
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/WEBHOOK/URL
```

### 3. Test the Python Crawler

```bash
# Activate the Python virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Test the crawler with example.com
node test_crawler.js
```

Check `crawler_test_results.json` to verify the scraper is working correctly.

### 4. Configure Your Sources

Edit `sources.json` or use the helper script:

```bash
# List current sources
node update_sources.js list

# Add a new website
node update_sources.js add website https://example.com

# Add a Twitter account
node update_sources.js add twitter https://x.com/username

# Remove a source
node update_sources.js remove website https://example.com
```

### 5. Run the Application

```bash
# Make sure the Python environment is activated
source venv/bin/activate

# Development mode
npm run dev

# Or build and run in production mode
npm run build
npm start
```

## Docker Deployment

### 1. Configure Environment Files

Create a `.env` file for Docker:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Build and Run with Docker Compose

```bash
# Build the Docker image
npm run docker:build
# or: docker-compose build

# Start the container
npm run docker:up
# or: docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
npm run docker:down
# or: docker-compose down
```

## Deployment to a VPS or Cloud Server

### 1. Prepare the Server

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y git nodejs npm python3 python3-pip python3-venv

# Install Docker (if using containerized deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Deploy the Application

#### Option A: Direct Deployment

```bash
# Clone the repository
git clone https://github.com/yourusername/trend-finder.git
cd trend-finder

# Setup and configure
./setup.sh
nano .env  # Edit configuration

# Run with PM2 for process management
npm install -g pm2
pm2 start dist/index.js --name trend-finder
pm2 save
pm2 startup
```

#### Option B: Docker Deployment

```bash
# Clone the repository
git clone https://github.com/yourusername/trend-finder.git
cd trend-finder

# Configure
cp .env.example .env
nano .env  # Edit configuration

# Deploy with Docker Compose
docker-compose up -d
```

## Setting Up Scheduled Jobs

### Using Node.js Cron (Built-in)

Edit `src/index.ts` to uncomment the cron job:

```typescript
// Uncomment to run the job every day at 5 PM
cron.schedule(`0 17 * * *`, async () => {
  console.log(`Starting process to generate draft...`);
  await handleCron();
});
```

### Using System Cron

For server deployments, you can use system cron:

```bash
# Edit crontab
crontab -e

# Add a job to run at 5 PM daily
0 17 * * * cd /path/to/trend-finder && source venv/bin/activate && npm start
```

## Troubleshooting

### Python and Crawl4AI Issues

```bash
# Check Python environment
source venv/bin/activate
python --version

# Verify Crawl4AI installation
pip show crawl4ai

# Run Crawl4AI diagnostics
python -c "from crawl4ai.doctor import run_doctor_checks; run_doctor_checks()"

# Check Playwright browsers
python -m playwright install chromium
```

### Node.js Issues

```bash
# Check Node.js and npm versions
node --version
npm --version

# Reinstall dependencies
rm -rf node_modules
npm ci
```

### Docker Issues

```bash
# Check Docker logs
docker-compose logs -f

# Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Updating the Application

```bash
# Pull latest changes
git pull

# Update dependencies
./setup.sh

# Rebuild (if necessary)
npm run build

# Restart the application
pm2 restart trend-finder
# OR for Docker:
docker-compose down && docker-compose up -d
```

## Monitoring and Logs

### Direct Deployment

```bash
# View logs with PM2
pm2 logs trend-finder

# Monitor processes
pm2 monit
```

### Docker Deployment

```bash
# View logs
docker-compose logs -f

# Check container status
docker-compose ps
```

## Security Considerations

1. **API Keys**: Keep your `.env` file secure and never commit it to version control.

2. **Docker Security**: Regularly update the base images with `docker-compose pull`.

3. **Updates**: Keep dependencies updated with `npm audit fix` and `pip install -U crawl4ai`.

4. **Access Control**: Restrict access to the server and SSH using key-based authentication.

5. **Firewall**: Configure a firewall to allow only necessary ports.

## Backup and Recovery

1. **Configuration Backup**: Regularly backup your `.env` and `sources.json` files.

2. **Database Backup**: If you add a database in the future, set up automated backups.

3. **Docker Volumes**: If using persistent Docker volumes, back them up regularly.

## Advanced Configuration

### Customizing Crawl4AI Options

Edit `src/services/crawler.py` to modify the crawler behavior:

```python
# Configure browser options
browser_cfg = BrowserConfig(
    headless=True,  # Set to False for debugging
    verbose=True,   # Enable for more logs
    timeout=90000   # Increase timeout for slow sites
)

# Configure extraction options
run_cfg = CrawlerRunConfig(
    cache_mode=CacheMode.USE_CACHE,  # Use cache or BYPASS_CACHE
    word_count_threshold=15,  # Minimum words for content
    wait_for_timeout=15000,  # Wait longer for content to load
)
```

### Multiple Notification Channels

To send notifications to multiple channels, edit `src/services/sendDraft.ts` to support multiple destinations.
