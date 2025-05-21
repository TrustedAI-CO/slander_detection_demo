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

target_person_analysis = st.text_input(
    "Target Person (optional)",
    placeholder="Name of the person being discussed",
    key="target_person_analysis",
)

# Add Start Analysis button
if st.button("Start Analysis", type="primary"):
    if natural_language_input:
        try:
            # Generate queries using LLM
            with st.spinner("Generating search queries..."):
                search_requests = query_generator.generate_queries(
                    natural_language_input
                )

                if not search_requests.twitter and not search_requests.youtube:
                    st.warning(
                        "No search queries could be generated. Please try rephrasing your input."
                    )
                else:
                    st.session_state.search_requests = search_requests
                    st.success("Search queries generated successfully!")

                    # Always clear previous results
                    st.session_state.search_results = []

                    # Display Twitter queries
                    st.subheader("Generated Search Requests")
                    # # Display YouTube queries
                    # for i, query in enumerate(search_requests.youtube, 1):
                    #     with st.expander(f"[YouTube] {query.query}"):
                    #         st.markdown(f"""
                    #         **Description:**
                    #         {query.description}
                    #         """)

                    for i, query in enumerate(search_requests.twitter, 1):
                        with st.expander(f"[Twitter] {query.query}"):
                            st.markdown(f"""
                            **Description:**  
                            {query.description}  
                            
                            **Parameters:**
                            - Section: {query.section or "Not specified"}
                            - Language: {query.language or "Not specified"}
                            - Date Range: {query.start_date or "Not specified"} to {query.end_date or "Not specified"}
                            """)

                    # Retrieve search results
                    with st.spinner("Retrieving search results..."):
                        # # YouTube
                        # for query in search_requests.youtube:
                        #     try:
                        #         results = youtube_tool.search_videos(query=query.query)
                        #         if not results:
                        #             st.info(f"No YouTube results for: {query.query}")
                        #         for result in results:
                        #             st.session_state.search_results.append(
                        #                 {
                        #                     "source": "YouTube",
                        #                     "title": result.title,
                        #                     "author": result.channel_title,
                        #                     "text": result.description,
                        #                     "date": result.published_at,
                        #                     "engagement": "Video",
                        #                     "video_id": result.video_id,
                        #                 }
                        #             )
                        #     except Exception as e:
                        #         st.error(f"Error searching YouTube: {str(e)}")

                        # Twitter
                        for query in search_requests.twitter:
                            try:
                                results = twitter_tool.search_tweets(query=query.query)
                                if not results:
                                    st.info(f"No Twitter results for: {query.query}")
                                for result in results:
                                    st.session_state.search_results.append(
                                        {
                                            "source": "Twitter",
                                            "title": result.text[:100],
                                            "author": result.user.username,
                                            "text": result.text,
                                            "date": result.creation_date,
                                            "engagement": f"{result.favorite_count} likes, {result.retweet_count} retweets",
                                            "tweet_id": result.tweet_id,
                                        }
                                    )
                            except Exception as e:
                                st.error(f"Error searching Twitter: {str(e)}")

                    st.success("Search complete!")

                    # Display results
                    st.subheader("Search Results")
                    if not st.session_state.search_results:
                        st.info("No search results found.")
                    for i, result in enumerate(st.session_state.search_results, 1):
                        with st.expander(
                            f"[No.{i}] [{result['source']}] {result['title']}"
                        ):
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
                                        comments = youtube_tool.get_video_comments(
                                            result["video_id"]
                                        )
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

                    # Automatically start analysis
                    if st.session_state.search_results:
                        with st.spinner("Analyzing content..."):
                            try:
                                slander_analyzer = SlanderAnalyzer()
                                # Use the new batch analysis method
                                analyses = slander_analyzer.analyze_multiple_texts(
                                    st.session_state.search_results,
                                    target_person_analysis,
                                )

                                # Calculate overall analysis
                                overall_analysis = (
                                    slander_analyzer.calculate_overall_analysis(
                                        analyses
                                    )
                                )

                                # Store results with their analyses
                                st.session_state.all_results = []
                                for result, analysis in zip(
                                    st.session_state.search_results, analyses
                                ):
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

                                # Store overall analysis
                                st.session_state.overall_analysis = overall_analysis
                                st.success("Analysis complete!")

                                # Display analysis results
                                col1, col2 = st.columns([1, 1])
                                with col1:
                                    st.subheader("Overall Analysis")
                                    overall = st.session_state.overall_analysis
                                    # Overall risk score
                                    risk_color = (
                                        "red"
                                        if overall.combined_risk_score > 0.7
                                        else "orange"
                                        if overall.combined_risk_score > 0.3
                                        else "green"
                                    )
                                    st.markdown(
                                        f"""
                                        <div style='text-align: center; padding: 20px; background-color: {risk_color}20; border-radius: 10px;'>
                                            <h2 style='color: {risk_color};'>Overall Risk Score: {overall.combined_risk_score:.1%}</h2>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                    st.markdown("### Pattern Analysis")
                                    st.markdown(overall.pattern_analysis)

                                    st.markdown("### Cross-References")
                                    st.markdown(overall.cross_references)

                                with col2:
                                    st.subheader("Individual Results")
                                    for i, result in enumerate(
                                        st.session_state.all_results, 1
                                    ):
                                        with st.expander(
                                            f"Result {i}: {result['source']} - {result['author']}"
                                        ):
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

                                            # Context Analysis
                                            if hasattr(analysis, "context_analysis"):
                                                st.markdown("**Context Analysis:**")
                                                st.markdown(analysis.context_analysis)

                            except Exception as e:
                                st.error(f"An error occurred during analysis: {str(e)}")
                    else:
                        st.warning("No results to analyze.")

        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
    else:
        st.warning("Please enter a search description to begin analysis.")
