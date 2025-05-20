import streamlit as st
from dotenv import load_dotenv

from analysis.slander_analyzer import SlanderAnalyzer
from tools.query_generator import QueryGenerator
from tools.twitter_tool import TwitterTool
from tools.youtube_tool import YouTubeTool

# Load environment variables
load_dotenv()

# Initialize tools
twitter_tool = TwitterTool()
youtube_tool = YouTubeTool()
query_generator = QueryGenerator()

# Set page config
st.set_page_config(page_title="Slander Detector", page_icon="🔍", layout="wide")

# App title and description
st.title("🔍 Slander Detector")
st.markdown("""
This tool analyzes text for potential slanderous statements and provides a detailed assessment.
""")

# Create input section
st.subheader("Search Configuration")

# Input fields
natural_language_input = st.text_area(
    "Describe what you want to search for",
    placeholder="Enter a natural language description of what you want to search for (e.g., 'Find information about allegations of financial misconduct by a tech company CEO')",
    height=100,
)

if st.button("Generate Search Requests", type="primary"):
    if natural_language_input:
        try:
            # Generate queries using LLM
            search_requests = query_generator.generate_queries(natural_language_input)

            # Store the search requests in session state for later use
            st.session_state.search_requests = search_requests

        except Exception as e:
            st.error(f"Error generating search queries: {str(e)}")
    else:
        st.warning("Please enter a search description.")

if hasattr(st.session_state, "search_requests"):
    st.subheader("Generated Search Requests")

    # Display Twitter queries
    for i, query in enumerate(st.session_state.search_requests.twitter, 1):
        with st.expander(f"[Twitter] {query.query}"):
            st.markdown(f"""
            **Description:**  
            {query.description}  
            
            **Parameters:**
            - Section: {query.section or "Not specified"}
            - Min Retweets: {query.min_retweets or "Not specified"}
            - Min Likes: {query.min_likes or "Not specified"}
            - Min Replies: {query.min_replies or "Not specified"}
            - Language: {query.language or "Not specified"}
            - Date Range: {query.start_date or "Not specified"} to {query.end_date or "Not specified"}
            """)

    # Display YouTube queries
    for i, query in enumerate(st.session_state.search_requests.youtube, 1):
        with st.expander(f"[YouTube] {query.query}"):
            st.markdown(f"""
            **Description:**  
            {query.description}                      
            """)

if hasattr(st.session_state, "search_requests"):
    if st.button("Retrieve Search Results", type="primary"):
        if not hasattr(st.session_state, "search_results"):
            st.session_state.search_results = []
        with st.spinner("Retrieving search results..."):
            # Execute YouTube searches
            for query in st.session_state.search_requests.youtube:
                try:
                    results = youtube_tool.search_videos(query=query.query)
                    # Process and store results
                    for result in results:
                        st.session_state.search_results.append(
                            {
                                "source": "YouTube",
                                "title": result.title,
                                "author": result.channel_title,
                                "text": result.description,
                                "date": result.published_at,
                                "engagement": "Video",  # Placeholder for now
                                "video_id": result.video_id,
                            }
                        )
                except Exception as e:
                    st.error(f"Error searching YouTube: {str(e)}")

            # # Execute Twitter searches
            # for query in st.session_state.search_requests.twitter:
            #     try:
            #         results = twitter_tool.search_tweets(query=query.query)

            #         # Process and store results
            #         for result in results:
            #             st.session_state.search_results.append(
            #                 {
            #                     "source": "Twitter",
            #                     "title": result.text[:100],
            #                     "author": result.user.username,
            #                     "text": result.text,
            #                     "date": result.creation_date,
            #                     "engagement": f"{result.favorite_count} likes, {result.retweet_count} retweets",
            #                     "tweet_id": result.tweet_id,
            #                 }
            #             )
            #     except Exception as e:
            #         st.error(f"Error searching Twitter: {str(e)}")

            st.success("Search complete!")

if hasattr(st.session_state, "search_results"):
    # Display results in a structured format
    st.subheader("Search Results")
    for i, result in enumerate(st.session_state.search_results, 1):
        with st.expander(f"[No.{i}] [{result['source']}] {result['title']}"):
            st.markdown(f"""
            **Source:** {result["source"]}  
            **Channel/Author:** {result["author"]}  
            **Published:** {result["date"]}  
            **Description/Text:** {result["text"]}
            """)

            # Add a button to view comments for YouTube
            if result["source"] == "YouTube":
                if st.button("View Comments", key=f"comments_{i}"):
                    with st.spinner("Loading comments..."):
                        comments = youtube_tool.get_video_comments(result["video_id"])
                        if comments:
                            st.markdown("### Comments")
                            for comment in comments:
                                st.markdown(f"""
                                **{comment["author"]}** ({comment["published_at"]})  
                                {comment["text"]}  
                                Likes: {comment["like_count"]}
                                ---
                                """)
                        else:
                            st.info(
                                "No comments found or comments are disabled for this video."
                            )


if hasattr(st.session_state, "search_results"):
    # Add analysis section
    st.subheader("Analyze Results")
    target_person_analysis = st.text_input(
        "Target Person (optional)",
        placeholder="Name of the person being discussed",
        key="target_person_analysis",
    )

if hasattr(st.session_state, "search_results"):
    if st.button("Analyze All Results", type="primary"):
        if st.session_state.search_results:
            with st.spinner("Analyzing content..."):
                try:
                    slander_analyzer = SlanderAnalyzer()
                    st.session_state.all_results = []
                    for result in st.session_state.search_results:
                        try:
                            analysis = slander_analyzer.analyze_text(
                                result["text"], st.session_state.target_person_analysis
                            )
                            st.session_state.all_results.append(
                                {
                                    "source": result["source"],
                                    "author": result["author"],
                                    "text": result["text"],
                                    "date": result["date"],
                                    "engagement": result.get("engagement", ""),
                                    "analysis": analysis,
                                }
                            )
                        except Exception as e:
                            st.error(
                                f"Error analyzing result from {result.get('source', 'unknown source')}: {str(e)}"
                            )
                            continue
                    st.success("Analysis complete!")
                except Exception as e:
                    st.error(f"An error occurred during analysis: {str(e)}")
        else:
            st.warning("No results to analyze.")

if hasattr(st.session_state, "all_results"):
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Analysis Results")
        # Calculate overall statistics
        total_risk = sum(
            r["analysis"].risk_score for r in st.session_state.all_results
        ) / len(st.session_state.all_results)
        total_confidence = sum(
            r["analysis"].confidence_score for r in st.session_state.all_results
        ) / len(st.session_state.all_results)

        # Overall risk score
        risk_color = (
            "red" if total_risk > 0.7 else "orange" if total_risk > 0.3 else "green"
        )
        st.markdown(
            f"""
            <div style='text-align: center; padding: 20px; background-color: {risk_color}20; border-radius: 10px;'>
                <h2 style='color: {risk_color};'>Overall Risk Score: {total_risk:.1%}</h2>
                <p>Average Confidence: {total_confidence:.1%}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.subheader("Individual Results")
        for i, result in enumerate(st.session_state.all_results, 1):
            with st.expander(f"Result {i}: {result['source']} - {result['author']}"):
                st.markdown(f"""
                **Source:** {result["source"]}  
                **Author:** {result["author"]}  
                **Date:** {result["date"]}  
                **Engagement:** {result["engagement"]}  
                **Text:** {result["text"]}
                """)

                analysis = result["analysis"]

                # Risk Score
                risk_color = (
                    "red"
                    if analysis.risk_score > 0.7
                    else "orange"
                    if analysis.risk_score > 0.3
                    else "green"
                )
                st.markdown(
                    f"""
                    <div style='padding: 10px; background-color: {risk_color}20; border-radius: 5px;'>
                        <p style='color: {risk_color};'><strong>Risk Score:</strong> {analysis.risk_score:.1%}</p>
                        <p><strong>Confidence:</strong> {analysis.confidence_score:.1%}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Slanderous Statements
                if (
                    hasattr(analysis, "slanderous_statements")
                    and analysis.slanderous_statements
                ):
                    st.markdown("**Potentially Slanderous Statements:**")
                    for j, statement in enumerate(analysis.slanderous_statements, 1):
                        st.markdown(f"""
                        **Statement {j}:**  
                        Risk Level: {statement["risk_level"]}  
                        Context: {statement["context"]}  
                        Reasoning: {statement["reasoning"]}
                        """)
                else:
                    st.info("No potentially slanderous statements detected.")

                # Context Analysis
                if hasattr(analysis, "context_analysis"):
                    st.markdown("**Context Analysis:**")
                    st.markdown(analysis.context_analysis)
