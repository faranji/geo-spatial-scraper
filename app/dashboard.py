import sys
import os

# Python'a "src" klasörünün nerede olduğunu kesin olarak öğretiyoruz
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

import streamlit as st
import pandas as pd
import pydeck as pdk
from src.database_manager import DatabaseManager, SpatialGrid, Venue

# --- SETTINGS ---
st.set_page_config(page_title="Live Map Scanning", page_icon=":smirk_cat:", layout="wide")

# --- RENK PALETİ ---
def get_color_by_status(status):
    if status == "Completed":
        return [46, 204, 113, 40] 
    elif status == "Processing":
        return [241, 196, 15, 120]  
    else:
        return [128, 128, 128, 15]  

@st.cache_data(ttl=15)
def fetch_grid_data():
    try:
        db_session = DatabaseManager().db
        grids = db_session.query(SpatialGrid).all()
        
        grid_list = []
        for g in grids:
            polygon = [
                [g.min_lon, g.min_lat], [g.max_lon, g.min_lat],
                [g.max_lon, g.max_lat], [g.min_lon, g.max_lat]
            ]
            grid_list.append({
                "id": g.id, "status": g.status,
                "coordinates": polygon, "color": get_color_by_status(g.status)
            })
        return pd.DataFrame(grid_list)
    except Exception as e:
        return pd.DataFrame(columns=["id", "status", "coordinates", "color"])

@st.cache_data(ttl=15)
def fetch_venues_data():
    try:
        db_session = DatabaseManager().db
        venues = db_session.query(Venue).all()
        
        venue_list = []
        for v in venues:
            venue_list.append({
                "name": v.name,
                "category": v.category,
                "latitude": v.latitude,
                "longitude": v.longitude,
                "rating": v.rating
            })

        if not venue_list:
            return pd.DataFrame(columns=["name", "category", "latitude", "longitude", "rating"])
        return pd.DataFrame(venue_list)
    except Exception as e:
        return pd.DataFrame(columns=["name", "category", "latitude", "longitude", "rating"])


# --- LOAD DATA ---
df_grids = fetch_grid_data()
df_venues = fetch_venues_data()


st.title("Realtime Data Fetching Operation")

if not df_venues.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("📌 Total Venues Found", f"{len(df_venues):,}")
    c2.metric("🟩 Scanned Area (Grid)", len(df_grids[df_grids['status'] == 'Completed']) if not df_grids.empty else 0)
    c3.metric("⭐ Average Rating", f"{df_venues['rating'].mean():.2f}")

st.divider()


st.markdown("### 🔍 Detailed Search and Filtering")

col1, col2, col3 = st.columns(3)

search_query = col1.text_input("Search Venue Name (e.g., Starbucks, Bistro):", "")

if not df_venues.empty:
    category_options = df_venues['category'].unique().tolist()
else:
    category_options = []

selected_categories = col2.multiselect("Category Filter:", options=category_options, default=category_options)
min_rating = col3.slider("Minimum Rating:", 0.0, 5.0, 0.0, 0.5)

# Did user chose a filter?
is_filtered = bool(search_query.strip()) or (min_rating > 0.0) or (len(selected_categories) != len(category_options))

filtered_venues = df_venues.copy()

if is_filtered and not filtered_venues.empty:
    if search_query:
        filtered_venues = filtered_venues[filtered_venues['name'].str.contains(search_query, case=False, na=False)]
    if selected_categories:
        filtered_venues = filtered_venues[filtered_venues['category'].isin(selected_categories)]
    filtered_venues = filtered_venues[filtered_venues['rating'] >= min_rating]
else:
    # no search = clean map
    filtered_venues = pd.DataFrame(columns=df_venues.columns) if not df_venues.empty else pd.DataFrame()

if is_filtered:
    st.caption(f"Showing **{len(filtered_venues):,}** venues on the map based on filters.")
else:
    st.caption("Waiting for your search query...")


# --- dynamic map focus ---
map_lat = 41.0082
map_lon = 28.9784
map_zoom = 10

if not filtered_venues.empty:
    map_lat = filtered_venues['latitude'].mean()
    map_lon = filtered_venues['longitude'].mean()
    
    if len(filtered_venues) == 1:
        map_zoom = 14
    else:
        lat_diff = filtered_venues['latitude'].max() - filtered_venues['latitude'].min()
        lon_diff = filtered_venues['longitude'].max() - filtered_venues['longitude'].min()
        max_diff = max(lat_diff, lon_diff)
        
        if max_diff < 0.02:
            map_zoom = 12.5
        elif max_diff < 0.08:
            map_zoom = 11
        elif max_diff < 0.25:
            map_zoom = 9.5
        else:
            map_zoom = 8.5

view_state = pdk.ViewState(latitude=map_lat, longitude=map_lon, zoom=map_zoom, pitch=0)

# --- giant map ---
layers = []

if not df_grids.empty:
    grid_layer = pdk.Layer(
        "PolygonLayer", df_grids, get_polygon="coordinates",
        get_fill_color="color", get_line_color=[255, 255, 255, 25],
        line_width_min_pixels=1, pickable=False 
    )
    layers.append(grid_layer)

if not filtered_venues.empty:
    icon_data = {
        "url": "https://cdn-icons-png.flaticon.com/512/149/149059.png",
        "width": 512,
        "height": 512,
        "anchorY": 512 
    }
    
    filtered_venues['icon_data'] = [icon_data for _ in range(len(filtered_venues))]
    
    venue_layer = pdk.Layer(
        "IconLayer",
        filtered_venues,
        get_icon="icon_data",
        get_size=20,
        get_position=["longitude", "latitude"],
        pickable=True 
    )
    layers.append(venue_layer)

st.pydeck_chart(pdk.Deck(
    layers=layers, initial_view_state=view_state,
    tooltip={"html": "<b>{name}</b><br/>Category: {category}<br/>Rating: {rating}⭐"}
))

# --- detailed data table ---
st.markdown("### 📋 Filtered Venue List")

if not filtered_venues.empty:
    display_df = filtered_venues[['name', 'category', 'rating', 'latitude', 'longitude']].copy()
    
    display_df['google_maps'] = "https://www.google.com/maps/search/?api=1&query=" + display_df['latitude'].astype(str) + "," + display_df['longitude'].astype(str)
    
    display_df = display_df.sort_values(by="rating", ascending=False)
    display_df['rating'] = display_df['rating'].apply(lambda x: f"{x:.1f} ⭐")
    display_df = display_df[['name', 'category', 'rating', 'google_maps']]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=350, 
        column_config={
            "name": st.column_config.TextColumn("Venue Name", width="large"),
            "category": st.column_config.TextColumn("Category", width="medium"),
            "rating": st.column_config.TextColumn("Rating", width="small"),
            "google_maps": st.column_config.LinkColumn("Action", display_text="📍 View on Maps", width="small")
        }
    )
elif not is_filtered:
    st.info("👆 Enter a search query or select a category to see venues.")
else:
    st.warning("No venues found matching your search criteria.")