import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from googleapiclient.discovery import build
from pydantic import BaseModel

load_dotenv()


class YouTubeSearchResult(BaseModel):
    video_id: str
    title: str
    description: str
    channel_title: str
    published_at: str


class YouTubeTool:
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YouTube API key not found in environment variables")
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    def search_videos(self, query: str) -> List[YouTubeSearchResult]:
        """
        Search for videos related to the query
        """
        try:
            search_response = (
                self.youtube.search()
                .list(q=query, part="id,snippet", maxResults=5, type="video")
                .execute()
            )

            results = []
            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]

                # Get video details for more information
                video_response = (
                    self.youtube.videos().list(part="snippet", id=video_id).execute()
                )

                video_details = video_response["items"][0]["snippet"]

                result = YouTubeSearchResult(
                    video_id=video_id,
                    title=snippet["title"],
                    description=video_details["description"],
                    channel_title=snippet["channelTitle"],
                    published_at=snippet["publishedAt"],
                )
                results.append(result)

            return results
        except Exception as e:
            print(f"Error searching YouTube videos: {str(e)}")
            return []

    def get_video_comments(
        self, video_id: str, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get comments for a specific video
        """
        try:
            comments_response = (
                self.youtube.commentThreads()
                .list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=max_results,
                    textFormat="plainText",
                )
                .execute()
            )

            comments = []
            for item in comments_response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append(
                    {
                        "author": comment["authorDisplayName"],
                        "text": comment["textDisplay"],
                        "published_at": comment["publishedAt"],
                        "like_count": comment["likeCount"],
                    }
                )

            return comments
        except Exception as e:
            print(f"Error getting video comments: {str(e)}")
            return []


if __name__ == "__main__":
    # Initialize the YouTube tool
    youtube_tool = YouTubeTool()

    # Test video search
    print("Testing video search...")
    search_results = youtube_tool.search_videos("永野芽郁")
    print(f"\nFound {len(search_results)} videos:")
    for result in search_results:
        print(f"\nTitle: {result.title}")
        print(f"Channel: {result.channel_title}")
        print(f"Published: {result.published_at}")
        print(f"Video ID: {result.video_id}")
        print("-" * 50)

    # Test getting comments for the first video
    if search_results:
        print("\nTesting comment retrieval...")
        video_id = search_results[0].video_id
        comments = youtube_tool.get_video_comments(video_id, max_results=5)
        print(f"\nRetrieved {len(comments)} comments for video {video_id}:")
        for comment in comments:
            print(f"\nAuthor: {comment['author']}")
            print(f"Comment: {comment['text']}")
            print(f"Likes: {comment['like_count']}")
            print(f"Published: {comment['published_at']}")
            print("-" * 50)
