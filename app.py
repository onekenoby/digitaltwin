# app.py
import streamlit as st
import pandas as pd

from neo4j_utils import (
    get_country_codes,
    get_tracks_for_country,
    close_driver
)
from map_utils_pydeck import draw_tracks_map
from export_utils import df_from_segments, df_to_csv, df_to_json

st.set_page_config(page_title="Digital Twin Tracks", layout="wide")
st.title("🚆 Tracks by Country")

# ─── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")

    # Country picker
    country = st.selectbox(
        "Select Country Code",
        options=get_country_codes()
    )

    # Show button
    show_btn = st.button("▶ Show Tracks")

    # Export options
    export_fmt = st.radio("Export format", ["CSV", "JSON"])
    do_export   = st.button("Download Track List")

# ─── Main ───────────────────────────────────────────────────────
segments = []
if show_btn:
    segments = get_tracks_for_country(country)
    if not segments:
        st.warning(f"No track segments found for country '{country}'.")
    else:
        st.success(f"Loaded {len(segments)} segments for {country}.")

# 1) Show table
st.subheader("Track Segments")
if segments:
    df = df_from_segments(segments)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Click ▶ Show Tracks to load segments.")

# 2) Export
if do_export and segments:
    df = df_from_segments(segments)
    if export_fmt == "CSV":
        st.download_button(
            "Download CSV",
            data=df_to_csv(df),
            file_name=f"tracks_{country}.csv",
            mime="text/csv"
        )
    else:
        st.download_button(
            "Download JSON",
            data=df_to_json(df),
            file_name=f"tracks_{country}.json",
            mime="application/json"
        )

# 3) Map
st.subheader("Map View")
deck = draw_tracks_map(segments)
st.pydeck_chart(deck, use_container_width=True)

# ─── Cleanup ────────────────────────────────────────────────────
close_driver()
