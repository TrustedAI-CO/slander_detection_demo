# Slander Detection Bot

This project implements an AI-powered bot that detects potential slanderous content on the internet using LangChain and LangGraph.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/slander_detector.git
   cd slander_detector
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   YOUTUBE_API_KEY=your_youtube_api_key
   TWITTER_BEARER_TOKEN=your_twitter_bearer_token
   ```

## Project Structure

- `main.py`: Main entry point for the slander detection bot
- `tools/`: Directory containing API integration tools
  - `youtube_tool.py`: YouTube API integration
  - `twitter_tool.py`: Twitter API integration
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (API keys) 