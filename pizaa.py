import streamlit as st
import folium
import osmnx as ox
import pandas as pd
from opencage.geocoder import OpenCageGeocode
import os

st.set_page_config(page_title="Dehradun Pizza Route Optimizer")
st.title("🍕 Domino's Dehradun Route Optimizer")

OPENCAGE_API_KEY = "0d01f656fc7042dbb49dbbc548fd6d62"
geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

@st.cache_data
def load_branch_data():
    df = pd.read_csv("dataset_ddun.csv")
    return {row['Branch']: (row['Latitude'], row['Longitude']) for idx, row in df.iterrows()}

@st.cache_data
def get_coordinates_cached(address):
    query = f"{address}, Dehradun, India"
    result = geocoder.geocode(query)
    if result and len(result):
        return result[0]['geometry']['lat'], result[0]['geometry']['lng']
    return None, None

def compute_path(G, orig_node, dest_node):
    return ox.shortest_path(G, orig_node, dest_node, weight='length')

def load_or_create_graph(lat, lng, dist=4000):
    graph_path = "dehradun_graph.graphml"
    if os.path.exists(graph_path):
        G = ox.load_graphml(graph_path)
    else:
        G = ox.graph_from_point((lat, lng), dist=dist, network_type='drive')
        ox.save_graphml(G, graph_path)
    return G

def plot_route_map(start_coords, end_address):
    start_lat, start_lng = start_coords
    end_lat, end_lng = get_coordinates_cached(end_address)

    st.write("📍 Start Coordinates:", start_lat, start_lng)
    st.write("📍 End Coordinates:", end_lat, end_lng)

    if None in (start_lat, start_lng, end_lat, end_lng):
        st.error("❌ Geocoding failed: Delivery address could not be located.")
        return None

    try:
        G = load_or_create_graph(start_lat, start_lng, dist=4000)
    except ValueError as ve:
        st.error("❌ Failed to create or load graph: " + str(ve))
        return None

    try:
        orig_node = ox.distance.nearest_nodes(G, start_lng, start_lat)
        dest_node = ox.distance.nearest_nodes(G, end_lng, end_lat)
        path = compute_path(G, orig_node, dest_node)
        if not path or len(path) < 2:
            st.error("❌ Route could not be calculated.")
            return None
    except Exception as e:
        st.error(f"❌ Routing failed: {e}")
        return None

    route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]

    m = folium.Map(location=[start_lat, start_lng], zoom_start=13)
    folium.Marker([start_lat, start_lng], popup="Start (Branch)", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_lat, end_lng], popup="Delivery Destination", icon=folium.Icon(color='red')).add_to(m)
    folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.9).add_to(m)

    map_file = "optimized_dijkstra_map.html"
    m.save(map_file)
    return map_file

branch_coords = load_branch_data()
branches = list(branch_coords.keys())

selected_branch = st.selectbox("📍 Select Domino's Branch", branches)
destination = st.text_input("🏠 Enter Delivery Destination", placeholder="e.g. ONGC chowk, Dehradun")

if st.button("🚗 Get Route"):
    if selected_branch and destination:
        start_coords = branch_coords[selected_branch]
        map_file = plot_route_map(start_coords, destination)
        if map_file:
            st.success("✅ Route generated!")
            with open(map_file, 'r', encoding='utf-8') as f:
                st.components.v1.html(f.read(), height=600)
    else:
        st.warning("⚠️ Please select a branch and enter a delivery address.")
