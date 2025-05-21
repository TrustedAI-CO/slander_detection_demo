import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from utils.open_router_llm import ChatOpenRouter


class TwitterSearchQuery(BaseModel):
    query: str
    description: str
    section: Optional[str] = Field(None, description="Search section (top, latest)")
    start_date: Optional[datetime] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[datetime] = Field(None, description="End date (YYYY-MM-DD)")
    language: Optional[str] = Field(None, description="Language code (e.g., en, ja)")

    @field_validator("section")
    @classmethod
    def validate_section(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ["top", "latest"]:
            return "latest"
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) != 2:
            return "ja"
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
        return yaml_str.replace("```yaml", "").replace("```", "").strip()

    def generate_queries(
        self,
        natural_language_input: str,
    ) -> SearchQueries:
        """Generate search queries based on natural language input."""
        default_dates = self._get_default_dates()

        system_prompt = f"""
### ROLE AND CONTEXT
You are an expert search query generator specializing in social media analysis and information gathering.
Current date: {datetime.now().strftime("%Y-%m-%d")}
Note: Generate queries in the same language as the input text. For example, if the input is in Japanese, generate Japanese queries.

### OBJECTIVE
Generate effective search queries for Twitter and YouTube that will help gather comprehensive information about the given topic.
The queries should be:
1. Precise and targeted
2. Varied in approach and perspective
3. Platform-optimized
4. Time-relevant
5. Language-appropriate

### QUERY GENERATION GUIDELINES

Twitter Query Requirements:
- Use natural language without operators (AND, OR, NOT)
- Include relevant hashtags when appropriate
- Consider both popular (top) and recent (latest) content
- Set appropriate engagement thresholds
- Use language-specific terms and expressions
- Consider temporal relevance

YouTube Query Requirements:
- Focus on specific content types (news, interviews, discussions)
- Include relevant keywords and phrases
- Consider both recent and popular content
- Use language-specific search terms
- Target different content formats

### OUTPUT SPECIFICATION

Format: YAML with the following structure:
```yaml
twitter:
  - query: <search terms> 
    description: <purpose explanation> 
    section: <top or latest> 
    start_date: YYYY-MM-DD 
    end_date: YYYY-MM-DD 
    language: <language code> 
youtube:
  - query: <search terms> 
    description: <purpose explanation> 
```

### EXAMPLE OUTPUT
```yaml
twitter:
  - query: 永野芽郁 不倫
    description: Search for tweets discussing the alleged affair and leaked information about actress Nao Minami
    section: top
    start_date: 2024-04-21
    end_date: 2024-05-21
    language: ja
  - query: 永野芽郁 噂
    description: Search for tweets discussing rumors and truth about Nao Minami
    section: latest
    start_date: 2024-04-21
    end_date: 2024-05-21
    language: ja
youtube:
  - query: 永野芽郁 報道
    description: Search for news reports and coverage about the alleged affair
  - query: 永野芽郁 真相
    description: Search for interviews and discussions about the truth of the situation
```

### IMPORTANT RULES
1. Generate exactly 2 queries per platform
2. Do not use quotes for string values unless they contain special characters
3. Maintain 2-space indentation
4. Set appropriate engagement thresholds based on topic relevance
5. Use language codes matching the input language
6. Consider temporal context in date ranges
7. Write clear, specific descriptions
8. Ensure YAML formatting is valid
9. Default date range: {default_dates["start_date"]} to {default_dates["end_date"]}
10. Always format dates as strings in YYYY-MM-DD format
"""

        messages = [
            ("system", system_prompt),
            (
                "human",
                f"Generate search queries for the following topic: {natural_language_input}",
            ),
        ]

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # Get LLM response
                response = self.llm.invoke(messages)
                time.sleep(1)  # Sleep for 1 second after LLM call

                if not response or not response.content:
                    raise ValueError("Empty response from LLM")

                # Clean and parse YAML
                yaml_str = self._clean_yaml_response(response.content)
                if not yaml_str:
                    raise ValueError("Empty YAML string after cleaning")

                queries_dict = yaml.safe_load(yaml_str)
                if not queries_dict:
                    raise ValueError("Empty dictionary after YAML parsing")

                # Validate required keys
                if "twitter" not in queries_dict or "youtube" not in queries_dict:
                    raise ValueError(
                        "Missing required keys 'twitter' or 'youtube' in response"
                    )

                # Add default dates to Twitter queries if not specified
                for query in queries_dict.get("twitter", []):
                    query.setdefault("start_date", default_dates["start_date"])
                    query.setdefault("end_date", default_dates["end_date"])

                # Convert to Pydantic model
                return SearchQueries(**queries_dict)

            except Exception as e:
                last_error = e
                print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    continue
                else:
                    print(
                        f"All {max_retries} attempts failed. Last error: {str(last_error)}"
                    )
                    return SearchQueries(twitter=[], youtube=[])


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
