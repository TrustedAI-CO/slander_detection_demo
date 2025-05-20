# Slander Detection Bot

This project implements an AI-powered bot that detects potential slanderous content on the internet using LangChain and LangGraph. The bot can analyze content from YouTube and Twitter to identify potentially defamatory statements about a person or related to specific keywords.

## Features

- YouTube content analysis using YouTube Data API
- Twitter content analysis using Twitter API v2
- AI-powered slander detection using LangChain
- Workflow orchestration using LangGraph

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   ```

## Usage

Run the main script:
```bash
python main.py --query "person_name" --keywords "keyword1,keyword2"
```

## Project Structure

- `main.py`: Main entry point for the slander detection bot
- `tools/`: Directory containing API integration tools
  - `youtube_tool.py`: YouTube API integration
  - `twitter_tool.py`: Twitter API integration
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (API keys) 