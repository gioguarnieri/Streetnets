import streamlit as st
import pandas as pd
import geopandas as gpd
import osmnx as ox
import plotly.express as px
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from shapely.geometry import Polygon
import io
import os
import zipfile
from tempfile import TemporaryDirectory

st.set_page_config(page_title="Retrieve data", page_icon="📊", layout='wide')

st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("City Statistics")
st.write("This page provides basic statistics for a selected city's street network. Beware that the data is not updated in real-time, so it may not reflect the latest changes in the city's infrastructure and may take a long time to retrieve.")



group1 = ['motorway', 'motorway_link', 'trunk', 'trunk_link']
group2 = ['primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link']
group3 = group1 + group2

if 'center' not in st.session_state:
    st.session_state.center = [-23.533773, -46.625290]
if 'zoom' not in st.session_state:
    st.session_state.zoom = 10

if ('location' not in st.session_state):
    lat, lon = "-23.533773", "-46.625290"
else:
    lat, lon = st.session_state.location.location[0], st.session_state.location.location[1]

def map_callback():
    map_state_change = st.session_state.folium_map
    # When the user interacts with the map, register the clicked location
    if map_state_change['last_clicked']:
        loc = map_state_change['last_clicked']
        st.session_state.location = folium.Marker([loc['lat'], loc['lng']])
        st.session_state.zoom = map_state_change['zoom']

c1, c2 = st.columns(2)
with c1:
    input_method = st.radio("Select retrieve method:", ["Point", "Geocoding", "From bounding box", "Draw polygon", "Shapefile"], help = "Make sure the shapefile/polygon is in WGS84 (EPSG:4326) coordinate system for compatibility with OSMnx. The tool will attempt to reproject if a different CRS is detected.")
    match input_method:
        case "Point":
            st.write("#### Point")

            st.write("Click on the map to select a location or write below.")
            
            cc1, cc2 = st.columns(2)
            with cc1:
                lat = st.text_input("Latitude:", value=lat)
                if ('location' in st.session_state):
                    st.session_state.location.location[0] = lat
            with cc2:
                lon = st.text_input("Longitude:", value=lon)
                if ('location' in st.session_state):
                    st.session_state.location.location[1] = lon
            st.session_state.center = [float(lat), float(lon)]
            box_size = st.number_input("Box size (in meters):", min_value=1, max_value=10000, value=1000, step=100)
        case "Shapefile":
            st.write("#### Upload Shapefile")
            st.write("Upload a .zip file containing the .shp, .shx, and .dbf files.")
            
            uploaded_file = st.file_uploader("Choose a zip file", type="zip")
            
            if uploaded_file is not None:
                # Create a temporary directory to extract the zip
                with TemporaryDirectory() as tmpdir:
                    # Save the uploaded zip file to the temp directory
                    zip_path = os.path.join(tmpdir, "upload.zip")
                    with open(zip_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    try:
                        # Extract the zip file
                        with zipfile.ZipFile(zip_path, "r") as zip_ref:
                            zip_ref.extractall(tmpdir)
                        
                        # Recursively search for the .shp file
                        shp_file_path = None
                        for root, dirs, files in os.walk(tmpdir):
                            for file in files:
                                if file.endswith(".shp"):
                                    shp_file_path = os.path.join(root, file)
                                    break
                            if shp_file_path:
                                break
                        
                        if shp_file_path:
                            # Read the shapefile using Geopandas
                            gdf = gpd.read_file(shp_file_path)
                            
                            # Check and verify CRS (Coordinate Reference System)
                            if gdf.crs is None:
                                st.warning("Shapefile has no CRS defined. Assuming EPSG:4326 (Lat/Lon).")
                                gdf.set_crs("EPSG:4326", inplace=True)
                            else:
                                # Reproject to EPSG:4326 for OSMnx compatibility
                                gdf = gdf.to_crs("EPSG:4326")
                            
                            # Extract the Polygon (Handling multiple features by unionizing them)
                            # This creates a single Polygon or MultiPolygon covering all features
                            polygon_geom = gdf.geometry.unary_union
                            
                            # Save to session state for retrieval later
                            st.session_state['shapefile_geometry'] = polygon_geom
                            
                            # Update the map center based on the shapefile centroid
                            centroid = polygon_geom.centroid
                            st.session_state.center = [centroid.y, centroid.x]
                            st.session_state.zoom = 12
                            
                            st.success(f"Shapefile loaded successfully! Contains {len(gdf)} features.")
                            
                        else:
                            st.error("Invalid Zip: No .shp file found inside.")
                            
                    except Exception as e:
                        st.error(f"An error occurred while processing the file: {e}")


with c2:
    option = st.selectbox(
    "Network type:",
    ("all", "all_public", "bike", "drive", "drive_service", "walk"),
    index=3,
    placeholder="Select network type...",
    )
    match input_method:
        case "Point":
            st.write("### Map ")
            # State variables
            if ('location' not in st.session_state):
                st.session_state.location = folium.Marker(st.session_state.center)

            # Map creation
            m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom)
            fg = folium.FeatureGroup(name="Markers")
            fg.add_child(st.session_state.location)

            kw = {
                "color": "blue",
                "line_cap": "round",
                "fill": True,
                "fill_color": "red",
                "weight": 5,
            }
            bbox = ox.utils_geo.bbox_from_point(
                point=(float(lat), float(lon)),
                dist=box_size,
                # project_utm=True,
            )
            bbox = ox.utils_geo.bbox_to_poly(bbox).exterior.coords.xy
            folium.Rectangle(
                bounds=[[bbox[1][0], bbox[0][0]], [bbox[1][2], bbox[0][2]]],
                line_join="round",
                dash_array="5, 5",
                **kw,
            ).add_to(m)

            map_state_change = st_folium(
                m,
                key="folium_map",
                feature_group_to_add=fg,
                height=400,
                width='100%',
                on_change=map_callback,
                returned_objects=['last_clicked', 'zoom', 'bounds', 'center'],
                )



        case "Geocoding":
            st.write("#### Enter a geocoding query")
            city = st.text_input("Geocoding query:", "Caraguatatuba")
            latlon = ox.geocoder.geocode(city)
            gdf = ox.geocoder.geocode_to_gdf(city)

            # Map creation
            m = folium.Map(location=latlon, zoom_start=10)
            fg = folium.FeatureGroup(name="Markers")
            st.session_state.center = latlon
            st.session_state.location = folium.Marker(latlon)
            fg.add_child(st.session_state.location)
            gdf.explore(m=m, color='red', name='Geocoding Result', marker_kwds={'radius': 5})
            map_state_change = st_folium(
                m,
                key="folium_map",
                feature_group_to_add=fg,
                height=400,
                width='100%',
                on_change=map_callback,
                returned_objects=['last_clicked', 'zoom', 'bounds', 'center'],
                )


        case "From bounding box":
            st.write("#### Enter bounding box coordinates")
            bc1, bc2, bc3, bc4 = st.columns(4)
            min_lat = bc1.number_input("Min latitude:", value=-23.6, format="%.6f", min_value=-90.0, max_value=90.0)
            min_lon = bc2.number_input("Min longitude:", value=-46.7, format="%.6f", min_value=-180.0, max_value=180.0)
            max_lat = bc3.number_input("Max latitude:", value=-23.5, format="%.6f", min_value=-90.0, max_value=90.0)
            max_lon = bc4.number_input("Max longitude:", value=-46.6, format="%.6f", min_value=-180.0, max_value=180.0)
            bbox = [min_lat, min_lon, max_lat, max_lon]
            if min_lat >= max_lat or min_lon >= max_lon:
                st.error("Min latitude/longitude must be smaller than max latitude/longitude.")
                bbox = None
            if bbox:
                # Map creation
                m = folium.Map(location=[(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2], zoom_start=12)
                fg = folium.FeatureGroup(name="Bounding Box")
                fg.add_child(folium.Rectangle(bounds=[[bbox[0], bbox[1]], [bbox[2], bbox[3]]], color='blue', fill=True, fill_color='blue', fill_opacity=0.1))
                st.session_state.location = folium.Marker([(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2])
                fg.add_child(st.session_state.location)

                map_state_change = st_folium(
                    m,
                    key="folium_map",
                    feature_group_to_add=fg,
                    height=400,
                    width='100%',
                    on_change=map_callback,
                    returned_objects=['last_clicked', 'zoom', 'bounds', 'center'],
                )
        case "Draw polygon":
            st.write("#### Draw a polygon on the map")
            st.write("Click on the map to draw a polygon. Double-click to finish.")
            # Initialize the map
            m = folium.Map(location=st.session_state.center, zoom_start=10)
            # Create a feature group for the polygon
            fg = folium.FeatureGroup(name="Drawn Polygon")
            # Add a draw control to the map
            draw_control = Draw(
                draw_options={
                    'polyline': False,
                    'polygon': True,
                    'rectangle': True,
                    'circle': False,
                    'marker': False,
                },
                edit_options={
                    'edit': True,
                    'remove': True
                }
            )
            m.add_child(draw_control)
            # Add a marker for the center point
            st.session_state.location = folium.Marker(st.session_state.center)
            fg.add_child(st.session_state.location)
            map_state_change = st_folium(
                m,
                key="folium_map",
                feature_group_to_add=fg,
                height=400,
                width='100%',
                on_change=map_callback,
                returned_objects=['last_clicked', 'zoom', 'bounds', 'center', "all_drawings"],
            )
        case "Shapefile":
            st.write("### Map Preview")
            
            # Initialize Map
            m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom)
            fg = folium.FeatureGroup(name="Uploaded Shapefile")
            
            # Check if geometry exists in session state (uploaded successfully)
            if 'shapefile_geometry' in st.session_state:
                # Add the polygon to the map
                folium.GeoJson(
                    st.session_state['shapefile_geometry'],
                    style_function=lambda x: {'fillColor': 'blue', 'color': 'blue', 'weight': 2, 'fillOpacity': 0.3}
                ).add_to(fg)
                
                # Add a marker for the center
                folium.Marker(st.session_state.center, popup="Centroid").add_to(fg)
                
                # Fit bounds to the polygon
                bounds = st.session_state['shapefile_geometry'].bounds # (minx, miny, maxx, maxy)
                m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            else:
                st.info("Upload a .zip file on the left to see the map preview.")

            # Render the map
            st_folium(
                m,
                key="folium_map",
                feature_group_to_add=fg,
                height=400,
                width='100%',
                returned_objects=['last_clicked', 'zoom', 'bounds', 'center'],
            )
            
            

if st.button("Retrieve data"):

    match input_method:
        case "Point":
            G = ox.graph_from_point(
                center_point=(float(lat), float(lon)),
                dist=box_size,
                network_type=option,
                simplify=True,
                retain_all=True,
                truncate_by_edge=True
            )
        case "Geocoding":
            G = ox.graph_from_place(
                city,
                network_type=option,
                simplify=True,
                retain_all=True,
                truncate_by_edge=True
            )
        case "From bounding box":
            if bbox is None:
                st.error("Please enter a valid bounding box first.")
                st.stop()
            G = ox.graph_from_bbox(
                bbox = (bbox[1], bbox[0], bbox[3], bbox[2]),
                network_type=option,
                simplify=True,
                retain_all=True,
                truncate_by_edge=True
            )
        case "Draw polygon":
            # Get the drawn polygon from the map
            if not map_state_change.get("all_drawings"):
                st.error("Please draw a polygon on the map first.")
                st.stop()
            geojson_data = map_state_change["all_drawings"][0]
            if geojson_data["geometry"]["type"] != "Polygon":
                st.error("The drawn shape must be a polygon or rectangle.")
                st.stop()
            coordinates = geojson_data["geometry"]["coordinates"][0]  # First ring
            coords = []
            for cols in coordinates:
                coords.append((float(cols[0]), float(cols[1])))
            p = Polygon(coords)
            G = ox.graph_from_polygon(
                polygon=p,
                network_type=option,
                simplify=True,
                retain_all=True,
                truncate_by_edge=True
            )
        case "Shapefile":
            if 'shapefile_geometry' in st.session_state:
                with st.spinner("Retrieving graph from shapefile polygon..."):
                    try:
                        G = ox.graph_from_polygon(
                            polygon=st.session_state['shapefile_geometry'],
                            network_type=option,
                            simplify=True,
                            retain_all=True,
                            truncate_by_edge=True
                        )
                    except Exception as e:
                        st.error(f"Error retrieving graph: {e}")
                        st.stop()
            else:
                st.error("Please upload a valid shapefile first.")
                st.stop()
    nodes, edges = ox.graph_to_gdfs(G)

    st.write("### Network Data Retrieved")
    st.write(f"## Statistics for the graph retrieved")

    # Calculate basic statistics
    total_nodes = len(nodes)
    total_edges = len(edges)
    total_length = edges['length'].sum()
    avg_length = edges['length'].mean()

    edges["highway"] = edges.highway.map(lambda x: x[0] if isinstance(x, list) else x)
    edges["Groups"] = edges.highway.map(lambda x: 'A' if x in group1 else 'B' if x in group2 else 'C')

    # Highway type distribution
    highway_counts = edges['highway'].value_counts()

    # Group distribution
    group_counts = edges['Groups'].value_counts()
    group_percentages = (group_counts / total_edges * 100).round(2)
    stats_data = {
        "Metric": [
            "Total Nodes (Intersections)",
            "Total Edges (Street Segments)",
            "Total Street Length (m)",
            "Average Street Segment Length (m)",
            "Group A Percentage (%)",
            "Group B Percentage (%)",
            "Group C Percentage (%)",
        ],
        "Value": [
            total_nodes,
            total_edges,
            f"{total_length:.2f}",
            f"{avg_length:.2f}",
            f"{group_percentages.get('A', 0):.2f}",
            f"{group_percentages.get('B', 0):.2f}",
            f"{group_percentages.get('C', 0):.2f}",
        ]
    }

    stats_df = pd.DataFrame(stats_data)
    st.table(stats_df)

    plot1, plot2 = st.columns(2)
    with plot1:
        st.write("### Highway Type Distribution")
        # Highway type distribution
        fig_highway = px.pie(
            values=highway_counts.values,
            names=highway_counts.index,
            # title="Highway Types"
        )
        st.plotly_chart(fig_highway)
    with plot2:
        # Group distribution
        st.write("### Group Distribution")
        fig_groups = px.pie(
            values=group_counts.values,
            names=group_counts.index,
            # title="Groups",
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        st.plotly_chart(fig_groups)
    @st.fragment
    def interactive_map():
        st.write("### Map of the Retrieved Data")
        # Create a map with the retrieved data
        m = edges.explore(
            column='length',
            cmap='viridis',
            tooltip=['name', 'length', 'highway', 'Groups'],
            name='Street Segments'
        )
        # Add the nodes to the map
        nodes.explore(
            m=m,
            color='red',
            marker_kwds={'radius': 5, 'fill': True, 'fill_color': 'red', 'fill_opacity': 0.6},
            name='Intersections'
        )
        st_folium(m, width="100%", height=500)
        
    interactive_map()
    # Download options
    st.write("### Download Data")
    st.warning("The files will be downloaded as a zip containing multiple files.")

    @st.fragment
    def generate_files(_nodes, _edges):
        option2 = st.selectbox(
        "Download as:",
        ( "ESRI Shapefile", "GeoJSON", "Parquet", "Feather", "GPKG", "SQLite", "CSV"),
        index=0,
        placeholder="Select file extension...",
        )

        if option2 == "ESRI Shapefile":
            file_ext = "shp"
        else:
            file_ext = option2.lower()
        # Generate files in memory


        with TemporaryDirectory() as tmpdir:
            nodes_path = os.path.join(tmpdir, 'nodes.'+file_ext)
            edges_path = os.path.join(tmpdir, 'edges.'+file_ext)
            if option2 == "CSV":
                _nodes.to_csv(nodes_path, index=False)
                _edges.to_csv(edges_path, index=False)
            else:
                _nodes.to_file(nodes_path, index=False)
                _edges.to_file(edges_path, index=False)

            # Create a zip file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zf:
                for foldername, subfolders, filenames in os.walk(tmpdir):
                    for filename in filenames:
                        file_path = os.path.join(foldername, filename)
                        zf.write(file_path, os.path.relpath(file_path, tmpdir))
            zip_buffer.seek(0)
            zip_bytes = zip_buffer.getvalue()

        st.download_button(
            label="Download Data",
            data=zip_bytes,
            file_name='files.zip',
        )
    generate_files(nodes, edges)