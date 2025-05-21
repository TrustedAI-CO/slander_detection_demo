import time
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel

from utils.open_router_llm import ChatOpenRouter


class SlanderAnalysisResult(BaseModel):
    risk_score: float  # 0-1 scale
    context_analysis: str
    confidence_score: float  # 0-1 scale


class OverallAnalysis(BaseModel):
    combined_risk_score: float
    pattern_analysis: str
    cross_references: str


class SlanderAnalyzer:
    def __init__(self, model_name: str = "meta-llama/llama-4-maverick:free"):
        self.llm = ChatOpenRouter(model_name=model_name)

    def calculate_overall_analysis(
        self, results: List[SlanderAnalysisResult]
    ) -> OverallAnalysis:
        """Calculate overall analysis by aggregating individual results."""
        if not results:
            return OverallAnalysis(
                combined_risk_score=0.0,
                pattern_analysis="No content analyzed.",
                cross_references="No content analyzed.",
            )

        # Calculate weighted average risk score based on confidence
        total_weight = sum(r.confidence_score for r in results)
        if total_weight == 0:
            combined_risk = sum(r.risk_score for r in results) / len(results)
        else:
            combined_risk = (
                sum(r.risk_score * r.confidence_score for r in results) / total_weight
            )

        # Combine context analyses to identify patterns
        context_analyses = [r.context_analysis for r in results]
        combined_context = "\n\n".join(
            f"Content {i + 1}:\n{analysis}"
            for i, analysis in enumerate(context_analyses)
        )

        # Generate pattern analysis prompt
        pattern_prompt = f"""
Analyze the following content analyses to identify patterns and relationships:

{combined_context}

Provide a concise analysis of:
1. Common themes or patterns across the content
2. How different pieces of content relate to each other
3. Overall assessment of the combined risk

IMPORTANT: Respond in the same language as the text to be analyzed.

### OUTPUT FORMAT
You MUST respond with ONLY a YAML object in the following format. DO NOT include any other text or explanation:

```yaml
language: <language of the text to be analyzed>
pattern_analysis: |
    <analysis of patterns across all content in detected language>
cross_references: |
    <analysis of how different pieces of content relate to each other in detected language>
```
"""

        try:
            response = self.llm.invoke(
                [
                    (
                        "system",
                        "You are an expert legal analyst specializing in pattern recognition across multiple pieces of content.",
                    ),
                    ("human", pattern_prompt),
                ]
            )
            time.sleep(1)  # Sleep for 1 second after LLM call

            if not response or not response.content:
                raise ValueError("Empty response from LLM")

            # Extract YAML from response
            yaml_str = (
                response.content.replace("```yaml", "").replace("```", "").strip()
            )
            if not yaml_str:
                raise ValueError("Empty YAML string after cleaning")

            # Parse YAML
            analysis_dict = yaml.safe_load(yaml_str)
            if not analysis_dict:
                raise ValueError("Empty dictionary after YAML parsing")

            return OverallAnalysis(
                combined_risk_score=combined_risk,
                pattern_analysis=analysis_dict.get(
                    "pattern_analysis", "No pattern analysis available."
                ),
                cross_references=analysis_dict.get(
                    "cross_references", "No cross-reference analysis available."
                ),
            )

        except Exception as e:
            print(f"Error generating pattern analysis: {str(e)}")
            return OverallAnalysis(
                combined_risk_score=combined_risk,
                pattern_analysis="Error generating pattern analysis.",
                cross_references="Error generating cross-reference analysis.",
            )

    def analyze_multiple_texts(
        self, texts: List[Dict[str, str]], target_person: Optional[str] = None
    ) -> List[SlanderAnalysisResult]:
        """Analyze multiple texts in a single prompt for better context awareness."""

        # Format all texts into a single prompt
        formatted_texts = []
        for i, text_data in enumerate(texts, 1):
            formatted_text = f"""
Content {i}:
Source: {text_data.get("source", "Unknown")}
Author: {text_data.get("author", "Unknown")}
Date: {text_data.get("date", "Unknown")}
Text: {text_data.get("text", "")}
Engagement: {text_data.get("engagement", "N/A")}
---
"""
            formatted_texts.append(formatted_text)

        combined_text = "\n".join(formatted_texts)

        # Use the same prompt structure but with modified instructions
        prompt = """
### CONTEXT
You are an expert legal analyst specializing in defamation and slander detection. You will analyze multiple pieces of content together to identify patterns and relationships between potentially slanderous statements.

IMPORTANT: Respond in the same language as the input.

### ANALYSIS CRITERIA
1. False Statements
   - Identify statements that appear to be false or misleading
   - Consider if statements are presented as facts rather than opinions
   - Check for verifiable claims that could be proven false
   - Look for patterns across multiple pieces of content

2. Harmful Impact
   - Assess potential damage to reputation
   - Consider the reach and visibility of the content
   - Evaluate the severity of the allegations
   - Consider cumulative impact of multiple statements

3. Context Analysis
   - Consider the overall context and tone
   - Identify any mitigating factors
   - Note any disclaimers or opinion indicators
   - Analyze relationships between different pieces of content

4. Risk Assessment
   - Evaluate the likelihood of legal action
   - Consider the severity of potential consequences
   - Assess the credibility of the sources
   - Consider the combined risk from multiple sources

### OUTPUT FORMAT
You MUST respond with ONLY a YAML object in the following format. DO NOT include any other text or explanation:

```yaml
content_analyses:
  - content_index: <number>
    language: <language of the content>
    risk_score: <float between 0 and 1>
    context_analysis: |
        <detailed analysis of the overall context in detected language>
    confidence_score: <float between 0 and 1>
```

### CRITICAL RULES
1. You MUST respond with ONLY the YAML object
2. Use proper indentation (2 spaces) for all fields
3. Use the | character for multi-line text fields
4. Keep single-line fields without the | character
5. All risk_score and confidence_score values must be floats between 0 and 1
6. The context_analysis must be a multi-line string using the | character
"""

        messages = [
            ("system", prompt),
            (
                "human",
                f"Content to analyze:\n{combined_text}\nTarget person (if specified): {target_person or 'Not specified'}",
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

                # Extract YAML from response
                yaml_str = (
                    response.content.replace("```yaml", "").replace("```", "").strip()
                )
                if not yaml_str:
                    raise ValueError("Empty YAML string after cleaning")

                # Parse YAML
                analysis_dict = yaml.safe_load(yaml_str)
                if not analysis_dict:
                    raise ValueError("Empty dictionary after YAML parsing")

                # Validate structure
                if "content_analyses" not in analysis_dict:
                    raise ValueError("Missing required top-level key: content_analyses")

                # Convert each content analysis to SlanderAnalysisResult
                results = []
                for content_analysis in analysis_dict["content_analyses"]:
                    results.append(SlanderAnalysisResult(**content_analysis))

                return results

            except Exception as e:
                last_error = e
                print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    continue
                else:
                    print(
                        f"All {max_retries} attempts failed. Last error: {str(last_error)}"
                    )
                    # Return default analysis results
                    return [
                        SlanderAnalysisResult(
                            risk_score=0.0,
                            context_analysis="Analysis failed after multiple attempts. Please try again.",
                            confidence_score=0.0,
                        )
                        for _ in texts
                    ]
