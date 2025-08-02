import streamlit as st
import os
from tower_map_generator import generate_map

st.set_page_config(page_title="Tower Trilateration", layout="wide")
query_params = st.query_params  # ✅ updated

if "map" in query_params:
    map_file = "trilateration_tower_map.html"
    if os.path.exists(map_file):
        with open(map_file, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=800)
    else:
        st.error("Map file not found.")
else:
    st.title("📡 Tower Trilateration App")
    lat = st.number_input("Latitude", value=26.187, format="%.6f")
    lon = st.number_input("Longitude", value=91.697, format="%.6f")
    rsrp = st.number_input("RSRP (dBm)", value=-95)

    if st.button("Generate Map"):
        generate_map(lat, lon, rsrp)
        st.markdown(f"[Click here to view map in new tab](?map=true)", unsafe_allow_html=True)
