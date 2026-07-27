import streamlit as st
import geopandas as gpd
import osmnx as ox
import plotly.express as px
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw
from shapely.geometry import Polygon, box
import io
import os
import zipfile
from tempfile import TemporaryDirectory
from uuid import uuid4

from streetnets_app.config import deep_analysis_enabled

DEEP_ANALYSIS = deep_analysis_enabled()

st.title("City Statistics")
st.write("This page provides basic statistics for a selected city's street network. Beware that the data is not updated in real-time, so it may not reflect the latest changes in the city's infrastructure and may take a long time to retrieve.")



group1 = ['motorway', 'motorway_link', 'trunk', 'trunk_link']
group2 = ['primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link']
group3 = group1 + group2

if 'center' not in st.session_state:
    st.session_state.center = [-23.533773, -46.625290]
if 'zoom' not in st.session_state:
    st.session_state.zoom = 10
if 'pt_lat' not in st.session_state:
    st.session_state.pt_lat = -23.533773
    st.session_state.pt_lon = -46.625290


@st.cache_data(show_spinner=False)
def geocode_place(query):
    """Cache Nominatim lookups so typing/reruns don't re-hit the network."""
    return ox.geocoder.geocode(query), ox.geocoder.geocode_to_gdf(query)

def map_callback():
    map_state_change = st.session_state.folium_map
    # When the user clicks the map, use that point as the selected location
    if map_state_change['last_clicked']:
        loc = map_state_change['last_clicked']
        st.session_state.pt_lat = loc['lat']
        st.session_state.pt_lon = loc['lng']
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
                lat = st.number_input("Latitude:", key="pt_lat", min_value=-90.0, max_value=90.0, format="%.6f")
            with cc2:
                lon = st.number_input("Longitude:", key="pt_lon", min_value=-180.0, max_value=180.0, format="%.6f")
            st.session_state.center = [lat, lon]
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
                            polygon_geom = gdf.geometry.union_all()
                            
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
            # Map creation
            m = folium.Map(location=st.session_state.center, zoom_start=st.session_state.zoom)
            fg = folium.FeatureGroup(name="Markers")
            fg.add_child(folium.Marker([lat, lon]))

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
            try:
                latlon, gdf = geocode_place(city)
            except Exception:
                st.error(f"Could not find '{city}' on OpenStreetMap. Try a more specific query (e.g. 'City, Country').")
                st.stop()

            # Map creation
            m = folium.Map(location=latlon, zoom_start=10)
            fg = folium.FeatureGroup(name="Markers")
            st.session_state.center = list(latlon)
            fg.add_child(folium.Marker(latlon))
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
                fg.add_child(folium.Marker([(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]))

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
            fg.add_child(folium.Marker(st.session_state.center))
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
            
            

if st.button("Retrieve data", type="primary"):

    # Validate inputs before hitting the network
    polygon = None
    if input_method == "From bounding box" and bbox is None:
        st.error("Please enter a valid bounding box first.")
        st.stop()
    if input_method == "Draw polygon":
        if not map_state_change.get("all_drawings"):
            st.error("Please draw a polygon on the map first.")
            st.stop()
        geojson_data = map_state_change["all_drawings"][0]
        if geojson_data["geometry"]["type"] != "Polygon":
            st.error("The drawn shape must be a polygon or rectangle.")
            st.stop()
        coordinates = geojson_data["geometry"]["coordinates"][0]  # First ring
        polygon = Polygon([(float(cols[0]), float(cols[1])) for cols in coordinates])
    if input_method == "Shapefile" and 'shapefile_geometry' not in st.session_state:
        st.error("Please upload a valid shapefile first.")
        st.stop()

    try:
        with st.spinner("Retrieving network from OpenStreetMap... large areas can take a while."):
            match input_method:
                case "Point":
                    G = ox.graph_from_point(
                        center_point=(lat, lon),
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
                    G = ox.graph_from_bbox(
                        bbox=(bbox[1], bbox[0], bbox[3], bbox[2]),
                        network_type=option,
                        simplify=True,
                        retain_all=True,
                        truncate_by_edge=True
                    )
                case "Draw polygon":
                    G = ox.graph_from_polygon(
                        polygon=polygon,
                        network_type=option,
                        simplify=True,
                        retain_all=True,
                        truncate_by_edge=True
                    )
                case "Shapefile":
                    G = ox.graph_from_polygon(
                        polygon=st.session_state['shapefile_geometry'],
                        network_type=option,
                        simplify=True,
                        retain_all=True,
                        truncate_by_edge=True
                    )
    except Exception as e:
        st.error(f"Error retrieving the network: {e}")
        st.stop()

    nodes, edges = ox.graph_to_gdfs(G)
    edges["highway"] = edges.highway.map(lambda x: x[0] if isinstance(x, list) else x)
    edges["Groups"] = edges.highway.map(lambda x: 'A' if x in group1 else 'B' if x in group2 else 'C')

    # Capture the area of interest so the Deep Analysis page can compute
    # database-comparable density metrics (area in m²)
    if input_method == "Point":
        aoi = {"method": "point", "point": (lat, lon), "dist": box_size}
        # Same convention as the 18-city database: a (2·dist)² square
        area_m2 = float((2 * box_size) ** 2)
    else:
        match input_method:
            case "Geocoding":
                aoi_geom = gdf.union_all()
            case "From bounding box":
                aoi_geom = box(bbox[1], bbox[0], bbox[3], bbox[2])
            case "Draw polygon":
                aoi_geom = polygon
            case _:  # Shapefile
                aoi_geom = st.session_state['shapefile_geometry']
        aoi = {"method": input_method, "geometry": aoi_geom}
        area_m2 = float(ox.projection.project_geometry(aoi_geom)[0].area)

    # Keep the result in session state so it survives reruns
    # (changing any widget no longer makes the results disappear)
    st.session_state.retrieved = {
        "nodes": nodes,
        "edges": edges,
        "aoi": aoi,
        "area_m2": area_m2,
        "network_type": option,
        "token": uuid4().hex,
    }
    if DEEP_ANALYSIS:
        # Only kept for the Deep Analysis page; on a hosted server it would
        # just double each session's memory footprint.
        st.session_state.retrieved["graph"] = G

if "retrieved" in st.session_state:
    nodes = st.session_state.retrieved["nodes"]
    edges = st.session_state.retrieved["edges"]

    st.write("## Statistics for the graph retrieved")
    if DEEP_ANALYSIS:
        st.page_link("pages/Deep_analysis.py",
                     label="Go deeper: centrality, vulnerability, and database comparison",
                     icon="🔬")

    # Calculate basic statistics
    total_nodes = len(nodes)
    total_edges = len(edges)
    total_length = edges['length'].sum()
    avg_length = edges['length'].mean()

    # Highway type distribution
    highway_counts = edges['highway'].value_counts()

    # Group distribution
    group_counts = edges['Groups'].value_counts()
    group_percentages = (group_counts / total_edges * 100).round(2)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Intersections (nodes)", f"{total_nodes:,}")
    m2.metric("Street segments (edges)", f"{total_edges:,}")
    m3.metric("Total street length", f"{total_length/1000:,.1f} km")
    m4.metric("Avg. segment length", f"{avg_length:.1f} m")

    g1, g2, g3, _ = st.columns(4)
    g1.metric("Group A (highways)", f"{group_percentages.get('A', 0):.1f}%")
    g2.metric("Group B (arterials)", f"{group_percentages.get('B', 0):.1f}%")
    g3.metric("Group C (local)", f"{group_percentages.get('C', 0):.1f}%")

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
        st.caption("A = highways & trunks · B = arterial streets (primary/secondary/tertiary) · C = local streets")
    st.page_link("pages/Glossary.py", label="What do these terms mean? See the Glossary", icon="📖")

    @st.fragment
    def interactive_map():
        st.write("### Map of the Retrieved Data")
        # Very large networks make the folium map unresponsive; show a sample
        MAX_MAP_FEATURES = 30_000
        map_edges, map_nodes = edges, nodes
        if len(edges) > MAX_MAP_FEATURES:
            st.info(
                f"This network has {len(edges):,} street segments — the interactive map shows a "
                f"random sample of {MAX_MAP_FEATURES:,} to stay responsive. "
                "The download below always contains the full network."
            )
            map_edges = edges.sample(MAX_MAP_FEATURES, random_state=0)
        if len(nodes) > MAX_MAP_FEATURES:
            map_nodes = nodes.sample(MAX_MAP_FEATURES, random_state=0)
        tooltip_cols = [c for c in ['name', 'length', 'highway', 'Groups'] if c in map_edges.columns]
        m = map_edges.explore(
            column='length',
            cmap='viridis',
            tooltip=tooltip_cols,
            name='Street Segments'
        )
        # Add the nodes to the map
        map_nodes.explore(
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

    def flatten_for_export(gdf):
        """Turn the (u, v, key)/osmid index into columns and stringify list
        values, which most file drivers (Shapefile, GPKG, ...) cannot store."""
        out = gdf.reset_index()
        for col in out.columns:
            if col != out.geometry.name and out[col].dtype == object:
                out[col] = out[col].map(lambda v: ", ".join(map(str, v)) if isinstance(v, list) else v)
        return out

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
        _nodes = flatten_for_export(_nodes)
        _edges = flatten_for_export(_edges)


        with TemporaryDirectory() as tmpdir:
            nodes_path = os.path.join(tmpdir, 'nodes.'+file_ext)
            edges_path = os.path.join(tmpdir, 'edges.'+file_ext)
            if option2 == "CSV":
                _nodes.to_csv(nodes_path, index=False)
                _edges.to_csv(edges_path, index=False)
            elif option2 == "Parquet":
                _nodes.to_parquet(nodes_path, index=False)
                _edges.to_parquet(edges_path, index=False)
            elif option2 == "Feather":
                _nodes.to_feather(nodes_path, index=False)
                _edges.to_feather(edges_path, index=False)
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
            file_name=f'streetnets_{file_ext}.zip',
        )
    generate_files(nodes, edges)