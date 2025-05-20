import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

load_dotenv()


class TwitterUser(BaseModel):
    user_id: str
    username: str
    name: str
    follower_count: int
    following_count: int
    description: Optional[str] = None
    location: Optional[str] = None
    profile_pic_url: Optional[str] = None
    is_verified: bool = False
    is_blue_verified: bool = False


class Tweet(BaseModel):
    tweet_id: str
    text: str
    creation_date: str
    user: TwitterUser
    favorite_count: int
    retweet_count: int
    reply_count: int
    quote_count: int
    views: Optional[int] = None
    media_url: Optional[List[str]] = None
    video_url: Optional[str] = None
    language: Optional[str] = None


class TwitterSearchParams(BaseModel):
    query: str
    section: Optional[str] = Field(
        None, description="Search section (top, latest, etc.)"
    )
    min_retweets: Optional[int] = Field(
        1, ge=0, description="Minimum number of retweets"
    )
    min_likes: Optional[int] = Field(1, ge=0, description="Minimum number of likes")
    min_replies: Optional[int] = Field(0, ge=0, description="Minimum number of replies")
    limit: Optional[int] = Field(
        20, ge=1, le=20, description="Maximum number of results (1-20)"
    )
    start_date: Optional[str] = Field(
        None, description="Start date in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    language: Optional[str] = Field(None, description="Language code (e.g., en, ja)")
    continuation_token: Optional[str] = Field(None, description="Token for pagination")

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ["top", "latest"]:
            raise ValueError("section must be either 'top' or 'latest'")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) != 2:
            raise ValueError("language must be a 2-letter code (e.g., en, ja)")
        return v

    def validate_dates(self):
        """Validate date formats and ranges."""
        if self.start_date:
            try:
                datetime.strptime(self.start_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("start_date must be in YYYY-MM-DD format")

        if self.end_date:
            try:
                datetime.strptime(self.end_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("end_date must be in YYYY-MM-DD format")

        if self.start_date and self.end_date:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            if start > end:
                raise ValueError("start_date must be before end_date")

    def to_dict(self) -> dict:
        """Convert to dictionary, removing None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class TwitterTool:
    def __init__(self):
        self.api_key = os.getenv("RAPID_OLD_BIRD_KEY")
        if not self.api_key:
            raise ValueError("RapidAPI Twitter key not found in environment variables")
        self.base_url = "https://twitter154.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-host": "twitter154.p.rapidapi.com",
            "x-rapidapi-key": self.api_key,
        }

    def _process_tweet_data(self, tweet_data: Dict[str, Any]) -> Tweet:
        """Process raw tweet data into a Tweet object."""
        user_data = tweet_data.get("user", {})
        user = TwitterUser(
            user_id=user_data.get("user_id", ""),
            username=user_data.get("username", ""),
            name=user_data.get("name", ""),
            follower_count=user_data.get("follower_count", 0),
            following_count=user_data.get("following_count", 0),
            description=user_data.get("description"),
            location=user_data.get("location"),
            profile_pic_url=user_data.get("profile_pic_url"),
            is_verified=user_data.get("is_verified", False),
            is_blue_verified=user_data.get("is_blue_verified", False),
        )

        return Tweet(
            tweet_id=tweet_data.get("tweet_id", ""),
            text=tweet_data.get("text", ""),
            creation_date=tweet_data.get("creation_date", ""),
            user=user,
            favorite_count=tweet_data.get("favorite_count", 0),
            retweet_count=tweet_data.get("retweet_count", 0),
            reply_count=tweet_data.get("reply_count", 0),
            quote_count=tweet_data.get("quote_count", 0),
            views=tweet_data.get("views"),
            media_url=tweet_data.get("media_url"),
            video_url=tweet_data.get("video_url"),
            language=tweet_data.get("language"),
        )

    def search_tweets(
        self,
        query: str,
        section: Optional[str] = None,
        min_retweets: Optional[int] = 1,
        min_likes: Optional[int] = 1,
        min_replies: Optional[int] = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        language: Optional[str] = None,
        continuation_token: Optional[str] = None,
    ) -> List[Tweet]:
        """
        Search for tweets related to the query with advanced filtering options.

        Args:
            query: Search query string
            section: Search section (e.g., 'top', 'latest')
            min_retweets: Minimum number of retweets
            min_likes: Minimum number of likes
            min_replies: Minimum number of replies
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            language: Language code (e.g., 'en', 'ja')
            continuation_token: Token for pagination

        Returns:
            List of Tweet objects

        Raises:
            ValueError: If any parameters are invalid
            requests.RequestException: If the API request fails
        """
        try:
            # Create and validate search parameters
            search_params = TwitterSearchParams(
                query=query,
                section=section,
                min_retweets=min_retweets,
                min_likes=min_likes,
                min_replies=min_replies,
                limit=5,  # Always use 20 results
                start_date=start_date,
                end_date=end_date,
                language=language,
                continuation_token=continuation_token,
            )

            # Validate parameters
            search_params.validate_dates()

            # Make API request
            url = f"{self.base_url}/search/search"
            response = requests.get(
                url,
                headers=self.headers,
                params=search_params.to_dict(),
                timeout=30,  # Add timeout
            )
            response.raise_for_status()
            data = response.json()

            # Process results
            results = []
            for tweet_data in data.get("results", []):
                try:
                    tweet = self._process_tweet_data(tweet_data)
                    results.append(tweet)
                except Exception as e:
                    print(f"Error processing tweet: {str(e)}")
                    continue

            return results

        except requests.RequestException as e:
            print(f"API request failed: {str(e)}")
            if hasattr(e.response, "text"):
                print(f"Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"Error searching tweets: {str(e)}")
            raise


if __name__ == "__main__":
    # Initialize the Twitter tool
    twitter_tool = TwitterTool()

    # Test tweet search with various parameters
    print("Testing tweet search...")
    try:
        search_results = twitter_tool.search_tweets(
            query="永野芽郁 不倫",
            section="top",
            min_retweets=1,
            min_likes=1,
            start_date="2024-01-01",
            language="en",
        )

        print(f"\nFound {len(search_results)} tweets:")
        for tweet in search_results:
            print(f"\nTweet ID: {tweet.tweet_id}")
            print(f"Text: {tweet.text}")
            print(f"Author: @{tweet.user.username}")
            print(f"Created: {tweet.creation_date}")
            print(f"Likes: {tweet.favorite_count}")
            print(f"Retweets: {tweet.retweet_count}")
            print("-" * 50)
    except Exception as e:
        print(f"Error during test: {str(e)}")
