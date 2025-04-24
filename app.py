# app.py

import streamlit as st

# ─── Must be first Streamlit command! ───────────────────────────
st.set_page_config(page_title="Digital Twin Tracks", layout="wide")

import pandas as pd
from neo4j_utils import (
    get_country_codes,
    get_tracks_for_country,
    get_operationpoint_counts,
    get_station_list,
    get_all_pois,
    get_minimal_path,
    close_driver
)
from map_utils_pydeck import draw_tracks_map, draw_route_map
from export_utils import df_to_csv, df_to_json

# ─── Sidebar: select page ────────────────────────────────────────
page = st.sidebar.selectbox(
    "Page",
    ["Overview", "Shortest Path", "Speed vs Time", "POI Overview"]
)

# ─── Overview Page ───────────────────────────────────────────────
if page == "Overview":
    st.title("🚆 Tracks by Country – Overview")
    country = st.sidebar.selectbox("Country", get_country_codes())
    if st.sidebar.button("▶ Load Overview"):
        segments = get_tracks_for_country(country)
        counts   = get_operationpoint_counts(country)

        st.metric("Total Segments", len(segments))
        cols = st.columns(3)
        cols[0].metric("Stations", counts["Stations"])
        cols[1].metric("Switches", counts["Switches"])
        cols[2].metric("Stop Points", counts["StopPoints"])

        st.subheader("Station List")
        st.table(pd.DataFrame({"Station": get_station_list(country)}))

        st.subheader("Map on Tracks")
        st.pydeck_chart(draw_tracks_map(segments), use_container_width=True)

# ─── Shortest Path Page ───────────────────────────────────────────
elif page == "Shortest Path":
    st.title("⚡ Shortest Path Calculations")

    # New: pick country first, then list stations in that country
    country = st.sidebar.selectbox("Country", get_country_codes())
    stations = get_station_list(country)
    if not stations:
        st.warning(f"No stations found for country {country}.")
    else:
        start = st.sidebar.selectbox("Start Station", stations, index=0)
        end   = st.sidebar.selectbox("End Station",   stations, index=min(1, len(stations)-1))

        if st.sidebar.button("▶ Compute Shortest Path"):
            route = get_minimal_path(start, end)
            if route:
                stops = len(route[0]["cities"])
                dist  = route[0]["total_distance"]
                st.subheader("Route Details")
                st.dataframe(pd.DataFrame([{"Stops": stops, "Distance (km)": dist}]))

                st.subheader("Map of Route")
                st.pydeck_chart(draw_route_map(route[0]), use_container_width=True)
            else:
                st.error("No path found between the selected stations.")

# ─── Speed vs Time Page ───────────────────────────────────────────
elif page == "Speed vs Time":
    st.title("⏱️ Speed vs. Time Mode")

    # keep the same country→station flow
    country = st.sidebar.selectbox("Country", get_country_codes())
    stations = get_station_list(country)
    src = st.sidebar.selectbox("Start Station", stations)
    dst = st.sidebar.selectbox("End Station",   stations, index=min(1,len(stations)-1))
    mode = st.sidebar.selectbox("Metric", ["sectionlength", "traveltime"])

    if st.sidebar.button("▶ Compute"):
        route = get_minimal_path(src, dst, weight=mode)
        if route:
            stops = len(route[0]["cities"])
            total = route[0]["total_distance"]
            st.subheader(f"Route by {mode}")
            st.dataframe(pd.DataFrame([{"Stops": stops, f"Total ({mode})": total}]))

            st.subheader("Map of Route")
            st.pydeck_chart(draw_route_map(route[0]), use_container_width=True)
        else:
            st.error("No path found (or invalid metric).")

# ─── POI Overview Page ───────────────────────────────────────────
else:  # "POI Overview"
    st.title("📌 POI Overview")

    pois = get_all_pois()
    if not pois:
        st.info("No POIs found in the database.")
    else:
        df_pois = pd.DataFrame(pois)

        # filter by city
        cities = sorted(df_pois["city"].dropna().unique())
        selected_city = st.sidebar.selectbox("Filter by City", ["All"] + cities)

        if selected_city != "All":
            df_pois = df_pois[df_pois["city"] == selected_city]

        st.subheader("POIs")
        st.dataframe(df_pois[["city", "description", "website"]], use_container_width=True)

        if not df_pois.empty and df_pois.iloc[0].get("foto"):
            st.subheader("Photo Preview")
            st.image(
                df_pois.iloc[0]["foto"],
                caption=df_pois.iloc[0]["description"],
                use_container_width=True
            )

# ─── Cleanup ─────────────────────────────────────────────────────
close_driver()
