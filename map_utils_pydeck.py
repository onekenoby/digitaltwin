# map_utils_pydeck.py
import pydeck as pdk
import pandas as pd

def draw_tracks_map(segments):
    """
    Given a list of dicts with keys lon1,lat1,lon2,lat2,
    returns a pydeck.Deck with a PathLayer for those segments.
    """
    # 1) Build a DataFrame of paths (each is a list of two coords)
    paths = [
        [[rec["lon1"], rec["lat1"]], [rec["lon2"], rec["lat2"]]]
        for rec in segments
    ]
    df_paths = pd.DataFrame({"path": paths})

    # 2) PyDeck PathLayer
    layer = pdk.Layer(
        "PathLayer",
        df_paths,
        pickable=True,
        get_path="path",
        get_width=3,
        get_color=[30, 144, 255],  # DodgerBlue
        width_min_pixels=2
    )

    # 3) Center the view on Italy (approx)
    #   Or compute centroid from all coords:
    if segments:
        avg_lat = sum(r["lat1"] + r["lat2"] for r in segments) / (2*len(segments))
        avg_lon = sum(r["lon1"] + r["lon2"] for r in segments) / (2*len(segments))
    else:
        # fallback to Italy center
        avg_lat, avg_lon = 41.9, 12.5

    view_state = pdk.ViewState(latitude=avg_lat, longitude=avg_lon, zoom=6)

    # 4) Build the deck
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/streets-v11",
        height=800
    )
    return deck
