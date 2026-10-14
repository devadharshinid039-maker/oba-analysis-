import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from textblob import TextBlob

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="OBA Analysis with NLP", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background: #f4f7fb; }
    [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e6ebf2; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; padding-bottom: 2.5rem; }
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e8edf4; border-radius: 12px;
        padding: 16px 18px; box-shadow: 0 2px 8px rgba(25, 42, 70, 0.04);
    }
    [data-testid="stMetricLabel"] p { color: #697586; font-size: 0.84rem; }
    [data-testid="stMetricValue"] { color: #172b4d; font-weight: 700; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff; border-color: #e8edf4; border-radius: 12px;
        box-shadow: 0 2px 8px rgba(25, 42, 70, 0.04);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- HELPER FUNCTIONS ----------------
def classify(value):
    if value < 50:
        return "Low"
    elif value <= 75:
        return "Medium"
    return "High"

def analyze_sentiment(text):
    text = str(text).strip()
    if not text:
        return "Neutral"
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    return "Neutral"

def style_levels(dataframe):
    def color_level(value):
        if value == "Low":
            return "background-color: #dc2626; color: white"
        if value == "Medium":
            return "background-color: #f59e0b; color: black"
        if value == "High":
            return "background-color: #16a34a; color: white"
        return ""
    return dataframe.style.map(color_level, subset=["Level"])

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 📊 OBA Insights")
st.sidebar.caption("Outcome-Based Education Dashboard")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "CO Attainment", "PO Attainment", "Feedback Analysis", "Dataset"],
    label_visibility="collapsed"
)
st.sidebar.divider()
uploaded_file = st.sidebar.file_uploader("Upload student CSV", type=["csv"])
target = st.sidebar.slider("Target marks", min_value=0, max_value=100, value=60)
st.sidebar.caption("Marks columns such as CO1, CO2, and CO3 are detected automatically.")

if uploaded_file is None:
    st.sidebar.info("Showing sample student data. Upload a CSV to analyze your own class.")
    sample = pd.DataFrame({
        "Student": ["S001", "S002", "S003", "S004", "S005", "S006"],
        "CO1": [85, 40, 65, 90, 72, 48],
        "CO2": [80, 45, 70, 88, 68, 55],
        "CO3": [90, 50, 68, 92, 75, 42],
        "Feedback": [
            "The teaching is excellent",
            "The lessons are very difficult",
            "The course is okay",
            "I really enjoyed learning",
            "The examples are helpful",
            "I am unhappy with the unclear explanation"
        ]
    })
    df = sample.copy()
    st.download_button(
        "⬇️ Download sample CSV",
        sample.to_csv(index=False).encode("utf-8"),
        file_name="sample_students.csv",
        mime="text/csv"
    )
else:
    # ---------------- LOAD AND VALIDATE DATA ----------------
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as error:
        st.error(f"Could not read this CSV file: {error}")
        st.stop()

if df.empty:
    st.error("The uploaded CSV has no rows. Please upload a dataset with student records.")
    st.stop()

feedback_col = next((c for c in df.columns if str(c).strip().lower() == "feedback"), None)
id_cols = {"student", "student id", "student_id", "name", "id", "roll no", "roll_no"}
id_col = next((c for c in df.columns if str(c).strip().lower() in id_cols), df.columns[0])

# Numeric columns excluding the student identifier and feedback
candidate_cols = [c for c in df.columns if c not in [id_col, feedback_col]]
co_columns = []
for col in candidate_cols:
    converted = pd.to_numeric(df[col], errors="coerce")
    if converted.notna().any():
        df[col] = converted
        co_columns.append(col)

if not co_columns:
    st.error("No numeric marks columns were found. Add columns such as CO1, CO2, and CO3.")
    st.stop()

df[co_columns] = df[co_columns].fillna(0)
co_results = []
for col in co_columns:
    attainment = (df[col].ge(target).sum() / len(df)) * 100
    co_results.append({
        "CO": col,
        "Students meeting target": int(df[col].ge(target).sum()),
        "Attainment (%)": round(attainment, 2),
        "Level": classify(attainment)
    })
co_df = pd.DataFrame(co_results)

mapping = {
    "CO1": [3, 2, 1],
    "CO2": [2, 3, 2],
    "CO3": [1, 2, 3]
}
po_scores = [0.0, 0.0, 0.0]
po_weights = [0.0, 0.0, 0.0]
for co, attainment in zip(co_df["CO"], co_df["Attainment (%)"]):
    if co in mapping:
        for j, weight in enumerate(mapping[co]):
            po_scores[j] += attainment * weight
            po_weights[j] += weight

po_values = [
    round(po_scores[i] / po_weights[i], 2) if po_weights[i] else 0.0
    for i in range(3)
]
po_df = pd.DataFrame({
    "PO": ["PO1", "PO2", "PO3"],
    "Attainment (%)": po_values,
    "Level": [classify(v) for v in po_values]
})

if feedback_col:
    df[feedback_col] = df[feedback_col].fillna("").astype(str)
    df["Sentiment"] = df[feedback_col].apply(analyze_sentiment)
    feedback_results = df[[id_col, feedback_col, "Sentiment"]].rename(
        columns={id_col: "Student", feedback_col: "Feedback"}
    )
    counts = df["Sentiment"].value_counts().reindex(
        ["Positive", "Neutral", "Negative"], fill_value=0
    )
else:
    feedback_results = pd.DataFrame(columns=["Student", "Feedback", "Sentiment"])
    counts = pd.Series([0, 0, 0], index=["Positive", "Neutral", "Negative"])

average_scores = df[co_columns].mean(axis=1)
average_mark = float(average_scores.mean())
average_attainment = float(co_df["Attainment (%)"].mean())
students_meeting_target = int(average_scores.ge(target).sum())
score_bands = pd.cut(
    average_scores,
    bins=[-1, 49, 59, 74, 84, 100],
    labels=["0-49", "50-59", "60-74", "75-84", "85-100"]
).value_counts().reindex(["0-49", "50-59", "60-74", "75-84", "85-100"], fill_value=0)

st.title("Dashboard Overview" if page == "Dashboard" else page)
st.caption(
    f"Welcome back! Here's what's happening with your class. "
    f"Target marks: {target}/100."
)

if page == "Dashboard":
    metric_cols = st.columns(4)
    metric_cols[0].metric("Total Students", f"{len(df):,}")
    metric_cols[1].metric("COs Tracked", len(co_columns))
    metric_cols[2].metric("Average Marks", f"{average_mark:.1f}%")
    metric_cols[3].metric("CO Attainment", f"{average_attainment:.1f}%")

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("📊 CO-wise Average Marks")
        st.caption("Average marks by course outcome")
        mean_marks = df[co_columns].mean()
        fig, ax = plt.subplots(figsize=(7, 3.4))
        ax.bar(mean_marks.index, mean_marks.values, color="#3b82f6", width=0.58)
        ax.axhline(target, color="#f59e0b", linestyle="--", linewidth=1.5, label=f"Target {target}")
        ax.set_ylim(0, 105)
        ax.set_ylabel("Average marks")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.18)
        ax.legend(frameon=False)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with right, st.container(border=True):
        st.subheader("📈 Student Score Overview")
        st.caption("Average marks for each student")
        fig2, ax2 = plt.subplots(figsize=(7, 3.4))
        ax2.plot(range(len(df)), average_scores.values, color="#16a06a", marker="o", linewidth=2)
        ax2.axhline(target, color="#f59e0b", linestyle="--", linewidth=1.5, label=f"Target {target}")
        ax2.set_ylim(0, 105)
        ax2.set_ylabel("Average marks")
        if len(df) <= 12:
            ax2.set_xticks(range(len(df)), df[id_col].astype(str), rotation=30, ha="right")
        else:
            ax2.set_xlabel("Students (dataset order)")
        ax2.spines[["top", "right"]].set_visible(False)
        ax2.grid(axis="y", alpha=0.18)
        ax2.legend(frameon=False)
        fig2.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.subheader("🍩 Average Score Distribution")
        st.caption("Student counts by average-mark range")
        fig3, ax3 = plt.subplots(figsize=(6, 3.4))
        colors = ["#ef4444", "#f59e0b", "#eab308", "#3b82f6", "#22c55e"]
        if int(score_bands.sum()) > 0:
            ax3.pie(
                score_bands.values,
                labels=score_bands.index,
                colors=colors,
                autopct=lambda pct: f"{pct:.0f}%" if pct > 0 else "",
                startangle=90,
                wedgeprops={"width": 0.42, "edgecolor": "white"}
            )
        ax3.set_aspect("equal")
        fig3.tight_layout()
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)

    with right, st.container(border=True):
        st.subheader("🧾 Analysis Snapshot")
        st.caption("Summary of the currently loaded dataset")
        st.markdown(
            f"""
            - **{len(df):,}** student records analyzed
            - **{len(co_columns)}** course outcomes detected
            - **{students_meeting_target:,}** students meet the overall target
            - **{int(counts['Positive'] + counts['Neutral'] + counts['Negative']):,}** feedback comments analyzed
            """
        )
        st.progress(students_meeting_target / len(df), text="Students meeting overall target")

    st.subheader("📥 Download Reports")
    download_cols = st.columns(3)
    download_cols[0].download_button(
        "Download CO report",
        co_df.to_csv(index=False).encode("utf-8"),
        file_name="co_attainment.csv",
        mime="text/csv"
    )
    download_cols[1].download_button(
        "Download PO report",
        po_df.to_csv(index=False).encode("utf-8"),
        file_name="po_attainment.csv",
        mime="text/csv"
    )
    if feedback_col:
        download_cols[2].download_button(
            "Download feedback report",
            feedback_results.to_csv(index=False).encode("utf-8"),
            file_name="nlp_feedback_results.csv",
            mime="text/csv"
        )

elif page == "CO Attainment":
    st.caption("Students reaching the selected target for each course outcome.")
    st.dataframe(style_levels(co_df), use_container_width=True, hide_index=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(co_df["CO"], co_df["Attainment (%)"], color="#3b82f6")
    ax.axhline(50, linestyle="--", linewidth=1, color="#f59e0b", label="50%")
    ax.axhline(75, linestyle="--", linewidth=1, color="#16a06a", label="75%")
    ax.set_ylim(0, 105)
    ax.set_ylabel("Attainment (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.download_button(
        "⬇️ Download CO Attainment CSV",
        co_df.to_csv(index=False).encode("utf-8"),
        file_name="co_attainment.csv",
        mime="text/csv"
    )

elif page == "PO Attainment":
    st.caption("Example CO-to-PO mapping is used; customize it to match your institution.")
    st.dataframe(style_levels(po_df), use_container_width=True, hide_index=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(po_df["PO"], po_df["Attainment (%)"], color="#8b5cf6")
    ax.set_ylim(0, 105)
    ax.set_ylabel("Attainment (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.download_button(
        "⬇️ Download PO Attainment CSV",
        po_df.to_csv(index=False).encode("utf-8"),
        file_name="po_attainment.csv",
        mime="text/csv"
    )

elif page == "Feedback Analysis":
    st.subheader("💬 Student Feedback Sentiment")
    if not feedback_col:
        st.warning("No 'Feedback' column was found. Add one to your CSV to enable sentiment analysis.")
    else:
        sentiment_cols = st.columns(3)
        sentiment_cols[0].metric("Positive", int(counts["Positive"]))
        sentiment_cols[1].metric("Neutral", int(counts["Neutral"]))
        sentiment_cols[2].metric("Negative", int(counts["Negative"]))
        left, right = st.columns(2)
        with left:
            st.subheader("Sentiment Counts")
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.bar(counts.index, counts.values, color=["#22c55e", "#94a3b8", "#ef4444"])
            ax.set_ylabel("Comments")
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(axis="y", alpha=0.18)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        with right:
            st.subheader("Sentiment Distribution")
            fig2, ax2 = plt.subplots(figsize=(6, 3.5))
            ax2.pie(
                counts.values,
                labels=counts.index,
                colors=["#22c55e", "#94a3b8", "#ef4444"],
                autopct="%1.1f%%",
                startangle=90,
                wedgeprops={"width": 0.42, "edgecolor": "white"}
            )
            ax2.set_aspect("equal")
            fig2.tight_layout()
            st.pyplot(fig2, use_container_width=True)
            plt.close(fig2)
        st.dataframe(feedback_results, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download NLP Feedback Results",
            feedback_results.to_csv(index=False).encode("utf-8"),
            file_name="nlp_feedback_results.csv",
            mime="text/csv"
        )

else:
    st.subheader("📋 Student Dataset")
    st.caption("Preview and download the uploaded or sample student records.")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download cleaned dataset",
        df.to_csv(index=False).encode("utf-8"),
        file_name="student_analysis_data.csv",
        mime="text/csv"
    )

st.caption(
    "Note: TextBlob provides a simple English sentiment estimate; it may misclassify sarcasm, context, "
    "and Tamil or other non-English feedback. PO mapping is an example and should be customized."
)
