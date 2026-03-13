import glob
import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def find_project_root() -> str:
    """Walk up from this file to find pyproject.toml."""
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.exists(os.path.join(current, "pyproject.toml")):
            return current
        current = os.path.dirname(current)
    return os.getcwd()


def load_analysis_data(journals_dir: str) -> pd.DataFrame:
    """Load all analysis JSON files into a DataFrame."""
    pattern = os.path.join(journals_dir, "**", "*.analysis.json")
    files = sorted(glob.glob(pattern, recursive=True))

    records = []
    for filepath in files:
        try:
            with open(filepath) as f:
                data = json.load(f)
        except Exception:
            continue

        entry_date = data.get("entry_date", "unknown")

        for section_name, section_data in data.get("sections", {}).items():
            record = {
                "date": entry_date,
                "section": section_name,
                "sentiment_score": section_data["sentiment"]["score"],
                "sentiment_label": section_data["sentiment"]["label"],
                "keywords": section_data.get("keywords", []),
            }
            for emotion in ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]:
                record[emotion] = section_data["emotions"].get(emotion, 0.0)
            records.append(record)

        overall = data.get("overall", {})
        if overall:
            record = {
                "date": entry_date,
                "section": "overall",
                "sentiment_score": overall["sentiment"]["score"],
                "sentiment_label": overall["sentiment"]["label"],
                "keywords": overall.get("keywords", []),
            }
            for emotion in ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]:
                record[emotion] = overall["emotions"].get(emotion, 0.0)
            records.append(record)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")
    return df


def load_entry_markdown(journals_dir: str, date_str: str, namespace: str = "5MJ") -> str:
    """Load journal markdown for a specific date."""
    year = date_str[:4]
    path = os.path.join(journals_dir, year, f"{namespace}-{date_str}.md")
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def page_overview(df: pd.DataFrame):
    """Overview page with key metrics and trends."""
    st.header("Overview")

    if df.empty:
        st.warning("No analyzed entries found. Run `journal analyze` first.")
        return

    overall = df[df["section"] == "overall"]

    col1, col2, col3 = st.columns(3)

    with col1:
        total = len(overall)
        st.metric("Total Entries", total)

    with col2:
        if not overall.empty:
            avg_sent = overall["sentiment_score"].mean()
            st.metric("Avg Sentiment", f"{avg_sent:.2f}")

    with col3:
        # Streak: count consecutive days backwards from most recent
        if not overall.empty:
            dates = sorted(overall["date"].dt.date.unique(), reverse=True)
            streak = 0
            for i, d in enumerate(dates):
                if i == 0:
                    streak = 1
                    continue
                diff = (dates[i - 1] - d).days
                if diff == 1:
                    streak += 1
                else:
                    break
            st.metric("Current Streak", f"{streak} days")

    # Sentiment trend
    if not overall.empty and len(overall) > 1:
        st.subheader("Sentiment Trend")
        fig = px.line(
            overall,
            x="date",
            y="sentiment_score",
            markers=True,
            labels={"sentiment_score": "Score", "date": "Date"},
        )
        fig.update_layout(yaxis_range=[0, 1], height=300)
        st.plotly_chart(fig, use_container_width=True)


def page_mood_trends(df: pd.DataFrame):
    """Mood trends with sentiment and emotion charts."""
    st.header("Mood Trends")

    if df.empty:
        st.warning("No data available.")
        return

    sections = df[df["section"].isin(["morning", "evening"])]

    # Sentiment over time by section
    if not sections.empty:
        st.subheader("Sentiment by Time of Day")

        rolling_window = st.selectbox("Rolling average", ["None", "7-day", "30-day"])

        fig = go.Figure()
        for section_name in ["morning", "evening"]:
            sec_data = sections[sections["section"] == section_name].copy()
            if sec_data.empty:
                continue

            y_values = sec_data["sentiment_score"]
            if rolling_window == "7-day":
                y_values = y_values.rolling(7, min_periods=1).mean()
            elif rolling_window == "30-day":
                y_values = y_values.rolling(30, min_periods=1).mean()

            fig.add_trace(go.Scatter(
                x=sec_data["date"],
                y=y_values,
                mode="lines+markers",
                name=section_name.capitalize(),
            ))

        fig.update_layout(yaxis_range=[0, 1], height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Emotion distribution over time
    overall = df[df["section"] == "overall"]
    if not overall.empty:
        st.subheader("Emotion Distribution Over Time")
        emotions = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
        fig = go.Figure()
        for emotion in emotions:
            fig.add_trace(go.Scatter(
                x=overall["date"],
                y=overall[emotion],
                mode="lines",
                name=emotion.capitalize(),
                stackgroup="one",
            ))
        fig.update_layout(height=400, yaxis_title="Score")
        st.plotly_chart(fig, use_container_width=True)


def page_entry_explorer(df: pd.DataFrame, journals_dir: str):
    """Explore individual entries."""
    st.header("Entry Explorer")

    if df.empty:
        st.warning("No data available.")
        return

    overall = df[df["section"] == "overall"]
    available_dates = sorted(overall["date"].dt.date.unique(), reverse=True)

    if not available_dates:
        st.warning("No entries to explore.")
        return

    selected_date = st.selectbox(
        "Select date",
        available_dates,
        format_func=lambda d: d.strftime("%B %d, %Y"),
    )

    date_str = selected_date.strftime("%Y-%m-%d")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Journal Entry")
        md_content = load_entry_markdown(journals_dir, date_str)
        if md_content:
            st.markdown(md_content)
        else:
            st.info("Markdown file not found.")

    with col2:
        st.subheader("Analysis")
        entry_data = df[(df["date"].dt.date == selected_date) & (df["section"] == "overall")]
        if not entry_data.empty:
            row = entry_data.iloc[0]

            st.metric("Sentiment", f"{row['sentiment_label']} ({row['sentiment_score']:.2f})")

            emotions = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
            emotion_values = [row[e] for e in emotions]
            fig = px.bar(
                x=emotions,
                y=emotion_values,
                labels={"x": "Emotion", "y": "Score"},
                color=emotions,
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

            keywords = row.get("keywords", [])
            if keywords:
                st.write("**Keywords:**", ", ".join(keywords))


def page_insights(df: pd.DataFrame):
    """Aggregate insights and patterns."""
    st.header("Insights")

    if df.empty:
        st.warning("No data available.")
        return

    overall = df[df["section"] == "overall"]

    col1, col2 = st.columns(2)

    with col1:
        # Emotion distribution pie chart
        st.subheader("Emotion Distribution")
        emotions = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
        avg_emotions = {e: overall[e].mean() for e in emotions}
        fig = px.pie(
            names=list(avg_emotions.keys()),
            values=list(avg_emotions.values()),
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top keywords
        st.subheader("Top Keywords")
        all_keywords = []
        for kw_list in overall["keywords"]:
            if isinstance(kw_list, list):
                all_keywords.extend(kw_list)

        if all_keywords:
            from collections import Counter
            counts = Counter(all_keywords).most_common(15)
            kw_df = pd.DataFrame(counts, columns=["Keyword", "Count"])
            fig = px.bar(kw_df, x="Count", y="Keyword", orientation="h")
            fig.update_layout(height=350, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    # Day-of-week patterns
    if not overall.empty and len(overall) > 6:
        st.subheader("Mood by Day of Week")
        overall_copy = overall.copy()
        overall_copy["day_of_week"] = overall_copy["date"].dt.day_name()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        grouped = overall_copy.groupby("day_of_week")["sentiment_score"]
        avg_by_day = grouped.mean().reindex(day_order)
        fig = px.bar(
            x=avg_by_day.index,
            y=avg_by_day.values,
            labels={"x": "Day", "y": "Avg Sentiment"},
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


def run():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Journal Analytics",
        page_icon=None,
        layout="wide",
    )
    st.title("Journal Analytics Dashboard")

    root = find_project_root()
    journals_dir = os.path.join(root, "journals")

    df = load_analysis_data(journals_dir)

    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "Mood Trends", "Entry Explorer", "Insights"],
    )

    if page == "Overview":
        page_overview(df)
    elif page == "Mood Trends":
        page_mood_trends(df)
    elif page == "Entry Explorer":
        page_entry_explorer(df, journals_dir)
    elif page == "Insights":
        page_insights(df)


def main():
    """Entry point for journal-dashboard command."""
    run()


if __name__ == "__main__":
    run()
