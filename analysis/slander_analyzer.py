from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel

from utils.open_router_llm import ChatOpenRouter


class SlanderAnalysisResult(BaseModel):
    risk_score: float  # 0-1 scale
    slanderous_statements: List[Dict[str, str]]
    context_analysis: str
    confidence_score: float  # 0-1 scale


class SlanderAnalyzer:
    def __init__(self, model_name: str = "meta-llama/llama-4-maverick:free"):
        self.llm = ChatOpenRouter(model_name=model_name)

    def analyze_text(
        self, text: str, target_person: Optional[str] = None
    ) -> SlanderAnalysisResult:
        """Analyze text for potential slanderous content."""

        prompt = f"""
### CONTEXT
You are an expert legal analyst specializing in defamation and slander detection.
Text to analyze: {text}
Target person (if specified): {target_person or "Not specified"}

### ANALYSIS CRITERIA
1. False Statements
   - Identify statements that appear to be false or misleading
   - Consider if statements are presented as facts rather than opinions
   - Check for verifiable claims that could be proven false

2. Harmful Impact
   - Assess potential damage to reputation
   - Consider the reach and visibility of the content
   - Evaluate the severity of the allegations

3. Context Analysis
   - Consider the overall context and tone
   - Identify any mitigating factors
   - Note any disclaimers or opinion indicators

4. Risk Assessment
   - Evaluate the likelihood of legal action
   - Consider the severity of potential consequences
   - Assess the credibility of the source

### OUTPUT FORMAT
Analyze the text and provide your assessment in the following YAML format:

```yaml
risk_score: <float between 0 and 1>
slanderous_statements:
  - statement: <the potentially slanderous statement>
    context: <relevant context>
    risk_level: <high/medium/low>
    reasoning: <why this might be slanderous>
context_analysis: |
    <detailed analysis of the overall context>
confidence_score: <float between 0 and 1>
```

IMPORTANT: 
1. Use proper indentation (2 spaces) for all fields
2. Use the | character for multi-line text fields
3. Keep single-line fields without the | character
4. Be thorough but objective in your analysis
5. Consider both legal and ethical implications
6. Only use single quotes for the statement field.
"""

        # Get LLM response
        response = self.llm.invoke(prompt)
        response.content = response.content.replace('"', "`")
        print(response.content)

        # Extract YAML from response
        yaml_str = response.content.replace("```yaml", "").replace("```", "").strip()
        analysis_dict = yaml.safe_load(yaml_str)

        # Convert to Pydantic model
        return SlanderAnalysisResult(**analysis_dict)

    def analyze_social_media(
        self, content: Dict[str, any], platform: str
    ) -> SlanderAnalysisResult:
        """Analyze social media content (YouTube or Twitter) for potential slander."""

        # Format content based on platform
        if platform == "youtube":
            text = f"""
Title: {content.get("title", "")}
Description: {content.get("description", "")}
Channel: {content.get("channel_title", "")}
Comments: {content.get("comments", [])}
"""
        elif platform == "twitter":
            text = f"""
Tweet: {content.get("text", "")}
Author: {content.get("user", {}).get("username", "")}
Engagement: {content.get("favorite_count", 0)} likes, {content.get("retweet_count", 0)} retweets
"""
        else:
            raise ValueError(f"Unsupported platform: {platform}")

        return self.analyze_text(text)
