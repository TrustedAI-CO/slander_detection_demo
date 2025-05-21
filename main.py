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
st.set_page_config(page_title="誹謗中傷検出ツール", page_icon="🔍", layout="wide")

# App title and description
st.title("🔍 誹謗中傷検出ツール")
st.markdown("""
このツールはテキストを分析し、潜在的な誹謗中傷の可能性を詳細に評価します。\n
現状はTwitterとYouTubeのみの検索に対応しています。\n
問い合わせ先：tran-thien@trusted-ai.co \n
開発会社のホームページ：https://trusted-ai.co/
""")

# Create input section
st.subheader("検索設定")

# Input fields
natural_language_input = st.text_area(
    "検索したい内容を説明してください",
    placeholder="検索したい内容を自然言語で入力してください（例：「テクノロジー企業のCEOによる財務不正行為に関する情報を探す」）",
    height=100,
)

target_person_analysis = st.text_input(
    "対象人物（任意）",
    placeholder="議論の対象となる人物の名前",
    key="target_person_analysis",
)

# Add Start Analysis button
if st.button("分析開始", type="primary"):
    if natural_language_input:
        try:
            # Generate queries using LLM
            with st.spinner("検索クエリを生成中..."):
                search_requests = query_generator.generate_queries(
                    natural_language_input
                )

                if not search_requests.twitter and not search_requests.youtube:
                    st.warning(
                        "検索クエリを生成できませんでした。入力内容を言い換えてみてください。"
                    )
                else:
                    st.session_state.search_requests = search_requests
                    st.success("検索クエリが正常に生成されました！")

                    # Always clear previous results
                    st.session_state.search_results = []

                    # Display Twitter queries
                    st.subheader("生成された検索リクエスト")
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
                            **説明:**  
                            {query.description}  
                            
                            **パラメータ:**
                            - セクション: {query.section or "指定なし"}
                            - 言語: {query.language or "指定なし"}
                            - 日付範囲: {query.start_date or "指定なし"} から {query.end_date or "指定なし"}
                            """)

                    # Retrieve search results
                    with st.spinner("検索結果を取得中..."):
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
                                    st.info(f"「{query.query}」の検索結果はありませんでした")
                                for result in results:
                                    st.session_state.search_results.append(
                                        {
                                            "source": "Twitter",
                                            "title": result.text[:100],
                                            "author": result.user.username,
                                            "text": result.text,
                                            "date": result.creation_date,
                                            "engagement": f"{result.favorite_count} いいね, {result.retweet_count} リツイート",
                                            "tweet_id": result.tweet_id,
                                        }
                                    )
                            except Exception as e:
                                st.error(f"Twitter検索中にエラーが発生しました: {str(e)}")

                    st.success("検索が完了しました！")

                    # Display results
                    st.subheader("検索結果")
                    if not st.session_state.search_results:
                        st.info("検索結果が見つかりませんでした。")
                    for i, result in enumerate(st.session_state.search_results, 1):
                        with st.expander(
                            f"[No.{i}] [{result['source']}] {result['title']}"
                        ):
                            st.markdown(f"""
                            **ソース:** {result["source"]}  
                            **アカウント/著者:** {result["author"]}  
                            **投稿日時:** {result["date"]}  
                            **内容:** {result["text"]}
                            """)

                            # Add a button to view comments for YouTube
                            if result["source"] == "YouTube":
                                if st.button("コメントを表示", key=f"comments_{i}"):
                                    with st.spinner("コメントを読み込み中..."):
                                        comments = youtube_tool.get_video_comments(
                                            result["video_id"]
                                        )
                                        if comments:
                                            st.markdown("### コメント")
                                            for comment in comments:
                                                st.markdown(f"""
                                                **{comment["author"]}** ({comment["published_at"]})  
                                                {comment["text"]}  
                                                いいね数: {comment["like_count"]}
                                                ---
                                                """)
                                        else:
                                            st.info(
                                                "コメントが見つからないか、この動画ではコメントが無効になっています。"
                                            )

                    # Automatically start analysis
                    if st.session_state.search_results:
                        with st.spinner("コンテンツを分析中..."):
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
                                st.success("分析が完了しました！")

                                # Display analysis results
                                col1, col2 = st.columns([1, 1])
                                with col1:
                                    st.subheader("全体分析")
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
                                            <h2 style='color: {risk_color};'>総合リスクスコア: {overall.combined_risk_score:.1%}</h2>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                    st.markdown("### パターン分析")
                                    st.markdown(overall.pattern_analysis)

                                    st.markdown("### 相互参照")
                                    st.markdown(overall.cross_references)

                                with col2:
                                    st.subheader("個別結果")
                                    for i, result in enumerate(
                                        st.session_state.all_results, 1
                                    ):
                                        with st.expander(
                                            f"結果 {i}: {result['source']} - {result['author']}"
                                        ):
                                            st.markdown(f"""
                                            **ソース:** {result["source"]}  
                                            **投稿者:** {result["author"]}  
                                            **日付:** {result["date"]}  
                                            **エンゲージメント:** {result["engagement"]}  
                                            **テキスト:** {result["text"]}
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
                                                    <p style='color: {risk_color};'><strong>リスクスコア:</strong> {analysis.risk_score:.1%}</p>
                                                    <p><strong>信頼度:</strong> {analysis.confidence_score:.1%}</p>
                                                </div>
                                                """,
                                                unsafe_allow_html=True,
                                            )

                                            # Context Analysis
                                            if hasattr(analysis, "context_analysis"):
                                                st.markdown("**コンテキスト分析:**")
                                                st.markdown(analysis.context_analysis)

                            except Exception as e:
                                st.error(f"分析中にエラーが発生しました: {str(e)}")
                    else:
                        st.warning("分析する結果がありません。")

        except Exception as e:
            st.error(f"分析中にエラーが発生しました: {str(e)}")
    else:
        st.warning("分析を開始するには検索内容を入力してください。")
