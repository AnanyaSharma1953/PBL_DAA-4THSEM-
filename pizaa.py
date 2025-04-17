import streamlit as st
import folium
import osmnx as ox
import heapq
from opencage.geocoder import OpenCageGeocode

# 🔑 Set your OpenCage API key here
OPENCAGE_API_KEY = "0d01f656fc7042dbb49dbbc548fd6d62"
geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

# 🎯 Custom Dijkstra's implementation
def custom_dijkstra(G, source, target):
    dist = {node: float('inf') for node in G.nodes}
    prev = {node: None for node in G.nodes}
    dist[source] = 0
    visited = set()
    queue = [(0, source)]

    while queue:
        current_dist, current_node = heapq.heappop(queue)
        if current_node in visited:
            continue
        visited.add(current_node)

        if current_node == target:
            break

        for neighbor in G.neighbors(current_node):
            weight = G.edges[current_node, neighbor, 0].get('length', 1)
            alt = current_dist + weight
            if alt < dist[neighbor]:
                dist[neighbor] = alt
                prev[neighbor] = current_node
                heapq.heappush(queue, (alt, neighbor))

    path = []
    current = target
    while current is not None:
        path.append(current)
        current = prev[current]
    path.reverse()

    if path[0] != source:
        raise ValueError("No path found")

    return path, list(visited)

# 🌍 Geocoding using OpenCage
def get_coordinates(address):
    result = geocoder.geocode(address)
    if result and len(result):
        lat = result[0]['geometry']['lat']
        lng = result[0]['geometry']['lng']
        return lat, lng
    else:
        st.error(f"❌ Could not find coordinates for: {address}")
        return None, None

# 🗺️ Main plotting function
def plot_route_map(start_address, end_address):
    start_lat, start_lng = get_coordinates(start_address)
    end_lat, end_lng = get_coordinates(end_address)
    if not start_lat or not end_lat:
        return None

    G = ox.graph_from_point((start_lat, start_lng), dist=5000, network_type='drive')
    orig_node = ox.distance.nearest_nodes(G, start_lng, start_lat)
    dest_node = ox.distance.nearest_nodes(G, end_lng, end_lat)

    try:
        path, visited = custom_dijkstra(G, orig_node, dest_node)
    except ValueError as e:
        st.error(str(e))
        return None

    route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in path]
    visited_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in visited]

    m = folium.Map(location=[start_lat, start_lng], zoom_start=14)
    folium.Marker([start_lat, start_lng], popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker([end_lat, end_lng], popup="End", icon=folium.Icon(color='red')).add_to(m)
    for coord in visited_coords:
        folium.CircleMarker(coord, radius=2, color='gray', fill=True, fill_opacity=0.2).add_to(m)
    folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.9).add_to(m)

    map_file = "custom_dijkstra_map.html"
    m.save(map_file)
    return map_file

# 🎛️ Streamlit UI
st.set_page_config(page_title="Manual Dijkstra Visualizer")
st.title("🧠 Manual Dijkstra’s Route Finder with Folium Map")

st.markdown("Enter two locations to find the shortest path using your own Dijkstra algorithm, powered by OpenCage Geocoding.")

start_input = st.text_input("Start Location", placeholder="e.g. Vasant Vihar, Dehradun")
end_input = st.text_input("End Location", placeholder="e.g. Engineers Enclave, Dehradun")

if st.button("Find Route"):
    if start_input and end_input:
        map_file = plot_route_map(start_input, end_input)
        if map_file:
            st.success("✅ Route generated using Dijkstra!")
            st.components.v1.html(open(map_file, 'r').read(), height=600)
    else:
        st.warning("⚠️ Please enter both start and end locations.")
