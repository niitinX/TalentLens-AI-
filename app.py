from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from talentlens.io import load_candidates, load_job_description, save_ranked_candidates_csv
from talentlens.scoring import rank_candidates


st.set_page_config(page_title="TalentLens AI", page_icon="TL", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    .hero {
        padding: 1.25rem 1.5rem;
        border-radius: 1.25rem;
        background: linear-gradient(135deg, #101828 0%, #1d4ed8 55%, #0f766e 100%);
        color: white;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 1rem;
        background: rgba(17, 24, 39, 0.04);
        border: 1px solid rgba(17, 24, 39, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1 style="margin:0;">TalentLens AI</h1>
      <p style="margin:0.5rem 0 0; opacity:0.9;">Rank candidates like a recruiter using evidence, role fit, and trust signals.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_left, col_right = st.columns(2)
with col_left:
    jd_file = st.file_uploader("Upload job description", type=["txt", "md", "docx"])
with col_right:
    candidates_file = st.file_uploader("Upload candidates dataset", type=["jsonl", "json", "csv"])

job_text = st.text_area("Or paste the job description", height=220)
top_k = st.slider("Shortlist size", min_value=10, max_value=100, value=25, step=5)

if st.button("Rank candidates", type="primary"):
    if not job_text and not jd_file:
        st.error("Add a job description first.")
        st.stop()
    if not candidates_file:
        st.error("Upload a candidate dataset first.")
        st.stop()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        candidates_path = temp_dir_path / candidates_file.name
        candidates_path.write_bytes(candidates_file.getbuffer())

        if jd_file is not None:
            jd_path = temp_dir_path / jd_file.name
            jd_path.write_bytes(jd_file.getbuffer())
            job_text = load_job_description(jd_path)

        candidates = load_candidates(candidates_path)
        ranked = rank_candidates(job_text, candidates, top_k=top_k)

        if not ranked:
            st.warning("No candidates were returned by the ranker.")
            st.stop()

        rows = []
        for rank, item in enumerate(ranked, start=1):
            rows.append(
                {
                    "rank": rank,
                    "candidate_id": item.candidate.candidate_id,
                    "name": item.candidate.name,
                    "current_title": item.candidate.current_title,
                    "score": round(item.score, 4),
                    "reasons": " | ".join(item.reasons),
                    "flags": " | ".join(item.flags),
                }
            )

        frame = pd.DataFrame(rows)
        st.subheader("Ranked shortlist")
        st.dataframe(frame, use_container_width=True, hide_index=True)

        csv_path = temp_dir_path / "ranked_candidates.csv"
        save_ranked_candidates_csv(ranked, csv_path)
        st.download_button(
            label="Download ranked CSV",
            data=csv_path.read_bytes(),
            file_name="ranked_candidates.csv",
            mime="text/csv",
        )

        st.subheader("Top candidate details")
        selected = st.selectbox("Select a candidate", options=list(range(len(ranked))), format_func=lambda index: f"{ranked[index].candidate.name or ranked[index].candidate.candidate_id} - {ranked[index].candidate.current_title}")
        candidate_result = ranked[selected]
        left, right = st.columns(2)
        with left:
            st.metric("Score", f"{candidate_result.score:.3f}")
            st.write("Reasons")
            st.write(candidate_result.reasons)
        with right:
            st.write("Flags")
            st.write(candidate_result.flags)
            st.write("Score breakdown")
            st.json(candidate_result.breakdown)
