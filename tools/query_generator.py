from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from utils.open_router_llm import ChatOpenRouter


class TwitterSearchQuery(BaseModel):
    query: str
    description: str
    section: Optional[str] = Field(None, description="Search section (top, latest)")
    min_retweets: Optional[int] = Field(1, ge=0, description="Minimum retweets")
    min_likes: Optional[int] = Field(1, ge=0, description="Minimum likes")
    min_replies: Optional[int] = Field(0, ge=0, description="Minimum replies")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    language: Optional[str] = Field(None, description="Language code (e.g., en, ja)")

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ["top", "latest"]:
            return "latest"  # Default to 'top' instead of raising error
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) != 2:
            return "ja"  # Default to 'ja' instead of raising error
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date must be in YYYY-MM-DD format")
        return v


class YouTubeSearchQuery(BaseModel):
    query: str
    description: str


class SearchQueries(BaseModel):
    twitter: List[TwitterSearchQuery]
    youtube: List[YouTubeSearchQuery]


class QueryGenerator:
    def __init__(self, model_name: str = "meta-llama/llama-4-maverick:free"):
        self.llm = ChatOpenRouter(model_name=model_name)

    def _get_default_dates(self) -> Dict[str, str]:
        """Get default date range for recent content."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
        }

    def _clean_yaml_response(self, yaml_str: str) -> str:
        """Clean and validate YAML response from LLM."""
        # Remove markdown code block markers
        yaml_str = yaml_str.replace("```yaml", "").replace("```", "").strip()

        return yaml_str

    def generate_queries(
        self,
        natural_language_input: str,
    ) -> SearchQueries:
        """Generate search queries based on natural language input."""

        # Get default date range
        default_dates = self._get_default_dates()

        prompt = f"""
### CONTEXT
You are an expert search query generator for social media analysis.
Natural language input: {natural_language_input}

### TASK
Generate a set of search queries for Twitter and YouTube that will help gather relevant information.
Consider:
1. Different variations of the search terms
2. Including/excluding specific terms
3. Using platform-specific search operators
4. Focusing on different aspects of the topic
5. Keep the query short and concise. Only include words, separated by spaces, don't use AND, OR, NOT, etc.
6. Use single quotes for the query string

### OUTPUT FORMAT
Provide your search queries in the following YAML format:

```yaml
twitter:
  - query: 'search query string'
    description: 'explanation of what this query aims to find'
    section: 'top'
    min_retweets: 1
    min_likes: 1
    min_replies: 0
    start_date: '{default_dates["start_date"]}'
    end_date: '{default_dates["end_date"]}'
    language: 'en'
youtube:
  - query: 'search query string'
    description: 'explanation of what this query aims to find'
```

IMPORTANT:
1. Use proper indentation (2 spaces) for all fields
2. Generate 2 queries per platform
3. Make descriptions clear and specific
4. Use platform-specific search operators where appropriate
5. Consider different angles and perspectives
6. For Twitter queries:
   - Use 'section: top' for popular tweets
   - Set appropriate min_retweets and min_likes for quality filtering
   - Use language codes (e.g., 'en', 'ja') when relevant
   - Use date ranges when temporal context is important
   - Default date range: {default_dates["start_date"]} to {default_dates["end_date"]}
7. For YouTube queries:
   - Focus on recent and relevant content
   - Use specific search terms
   - Consider different content types (news, interviews, etc.)
8. Always use double quotes for strings in YAML
9. Ensure proper YAML formatting and indentation
"""

        try:
            # Get LLM response
            response = self.llm.invoke(prompt)

            # Clean and parse YAML
            yaml_str = self._clean_yaml_response(response.content)
            queries_dict = yaml.safe_load(yaml_str)

            # Add default dates to Twitter queries if not specified
            for query in queries_dict.get("twitter", []):
                if "start_date" not in query:
                    query["start_date"] = default_dates["start_date"]
                if "end_date" not in query:
                    query["end_date"] = default_dates["end_date"]

            # Convert to Pydantic model
            return SearchQueries(**queries_dict)

        except Exception as e:
            print(f"Error generating queries: {str(e)}")
            raise


if __name__ == "__main__":
    # Test the query generator
    generator = QueryGenerator()
    test_input = "永野芽郁　不倫　流出"

    try:
        queries = generator.generate_queries(test_input)
        print("\nGenerated Search Queries:")
        print("------------------------")

        print("\nTwitter Queries:")
        for query in queries.twitter:
            print(f"\nQuery: {query.query}")
            print(f"Description: {query.description}")
            if query.section:
                print(f"Section: {query.section}")
            if query.min_retweets:
                print(f"Min Retweets: {query.min_retweets}")
            if query.min_likes:
                print(f"Min Likes: {query.min_likes}")
            if query.language:
                print(f"Language: {query.language}")
            if query.start_date:
                print(f"Start Date: {query.start_date}")
            if query.end_date:
                print(f"End Date: {query.end_date}")

        print("\nYouTube Queries:")
        for query in queries.youtube:
            print(f"\nQuery: {query.query}")
            print(f"Description: {query.description}")

    except Exception as e:
        print(f"\nError during test: {str(e)}")
