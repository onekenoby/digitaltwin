# map_utils_pydeck.py
import pydeck as pdk
import pandas as pd

def draw_tracks_map(segments):
    """
    Render track segments as blue lines on a map.
    """
    paths = [
        [[rec["lon1"], rec["lat1"]], [rec["lon2"], rec["lat2"]]]
        for rec in segments
    ]
    df_paths = pd.DataFrame({"path": paths})

    layer = pdk.Layer(
        "PathLayer",
        df_paths,
        pickable=True,
        get_path="path",
        get_width=3,
        get_color=[30, 144, 255],  # DodgerBlue
        width_min_pixels=2
    )

    if segments:
        avg_lat = sum(r["lat1"] + r["lat2"] for r in segments) / (2 * len(segments))
        avg_lon = sum(r["lon1"] + r["lon2"] for r in segments) / (2 * len(segments))
    else:
        avg_lat, avg_lon = 41.9, 12.5

    view_state = pdk.ViewState(latitude=avg_lat, longitude=avg_lon, zoom=6)

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/streets-v11",
        height=800
    )

def draw_route_map(route):
    """
    Render a single route as a red line on a map.
    """
    coords = [[c["lon"], c["lat"]] for c in route.get("cities", [])]
    df = pd.DataFrame({"path": [coords]})

    layer = pdk.Layer(
        "PathLayer",
        df,
        get_path="path",
        get_color=[255, 0, 0],  # red
        get_width=5,
        width_min_pixels=2
    )

    if coords:
        center_lat = coords[0][1]
        center_lon = coords[0][0]
    else:
        center_lat, center_lon = 41.9, 12.5

    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7)

    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/streets-v11",
        height=600
    )
