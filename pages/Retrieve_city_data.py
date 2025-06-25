import streamlit as st
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
import plotly.express as px
from streamlit_folium import st_folium
import folium
import streamlit_js_eval

st.set_page_config(page_title="Retrieve data", page_icon="📊", layout='wide')

st.title("City Statistics")
st.write("This page provides basic statistics for a selected city's street network. Beware that the data is not updated in real-time, so it may not reflect the latest changes in the city's infrastructure and may take a long time to retrieve.")



group1 = ['motorway', 'motorway_link', 'trunk', 'trunk_link']
group2 = ['primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link']
group3 = group1 + group2
if ('location' not in st.session_state):
    lat, lon = "-23.533773", "-46.625290"
else:
    lat, lon = st.session_state.location.location[0], st.session_state.location.location[1]

c1, c2 = st.columns(2)
with c1:
    input_method = st.radio("Select retrieve method:", ["Point", "Geocoding", "From bounding box"])
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


with c2:
    match input_method:
        case "Point":
            st.write("### Map ")
            # State variables
            
            if ('center' not in st.session_state):
                st.session_state.center = lat, lon
            if 'zoom' not in st.session_state:
                st.session_state.zoom = 10

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

            def callback():
                map_state_change = st.session_state.folium_map
                # When the user interacts with the map
                # If the interaction includes a click
                if map_state_change['last_clicked']:
                    loc = map_state_change['last_clicked']
                    st.session_state.location = folium.Marker([loc['lat'], loc['lng']])
                    st.session_state.zoom = map_state_change['zoom']

            map_state_change = st_folium(
                m,
                key="folium_map",
                feature_group_to_add=fg,
                height=400,
                width='100%',
                on_change=callback,
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
            st.session_state.cecnter = latlon
            st.session_state.location = folium.Marker(latlon)
            fg.add_child(st.session_state.location)
            def callback():
                map_state_change = st.session_state.folium_map
                # When the user interacts with the map
                # If the interaction includes a click
                # print(map_state_change)
                if map_state_change['last_clicked']:
                    loc = map_state_change['last_clicked']
                    st.session_state.location = folium.Marker([loc['lat'], loc['lng']])
                    st.session_state.zoom = map_state_change['zoom']
            gdf.explore(m=m, color='red', name='Geocoding Result', marker_kwds={'radius': 5})
            map_state_change = st_folium(
                m,
                key="folium_map",
                feature_group_to_add=fg,
                height=400,
                width='100%',
                on_change=callback,
                returned_objects=['last_clicked', 'zoom', 'bounds', 'center'],
                )






        case "From bounding box":
            st.write("#### Enter bounding box coordinates")
            bbox = st.text_input("Bounding box (min_lat, min_lon, max_lat, max_lon):", "-23.6,-46.7,-23.5,-46.6")
            try:
                bbox = [float(coord) for coord in bbox.split(",")]
                if len(bbox) != 4:
                    raise ValueError("Bounding box must have 4 coordinates.")   
            except ValueError as e:
                st.error(f"Invalid bounding box format: {e}")
                bbox = None
            if bbox:
                # Create a bounding box polygon
                bbox_poly = ox.utils_geo.bbox_to_poly(bbox)
                
                # Map creation
                m = folium.Map(location=[(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2], zoom_start=12)
                fg = folium.FeatureGroup(name="Bounding Box")
                fg.add_child(folium.Rectangle(bounds=[[bbox[0], bbox[1]], [bbox[2], bbox[3]]], color='blue', fill=True, fill_color='blue', fill_opacity=0.1))
                st.session_state.location = folium.Marker([(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2])
                fg.add_child(st.session_state.location)
                
                def callback():
                    map_state_change = st.session_state.folium_map
                    # When the user interacts with the map
                    # If the interaction includes a click
                    if map_state_change['last_clicked']:
                        loc = map_state_change['last_clicked']
                        st.session_state.location = folium.Marker([loc['lat'], loc['lng']])
                        st.session_state.zoom = map_state_change['zoom']
                
                map_state_change = st_folium(
                    m,
                    key="folium_map",
                    feature_group_to_add=fg,
                    height=400,
                    width='100%',
                    on_change=callback,
                    returned_objects=['last_clicked', 'zoom', 'bounds', 'center'],
                )
            

if st.button("Retrieve data"):
    match input_method:
        case "Point":
            G = ox.graph_from_point(
                center_point=(float(lat), float(lon)),
                dist=box_size,
                network_type='drive',
                simplify=True,
                retain_all=True
            )
        case "Geocoding":
            G = ox.graph_from_place(
                city,
                network_type='drive',
                simplify=True,
                retain_all=True
            )
        case "From bounding box":
            G = ox.graph_from_bbox(
                north=bbox[2],
                south=bbox[0],
                east=bbox[3],
                west=bbox[1],
                network_type='drive',
                simplify=True,
                retain_all=True
            )

    nodes, edges = ox.graph_to_gdfs(G)
    
    if nodes is not None and edges is not None:
        st.write("### Network Data Retrieved")
        ### make a map with the retrieved data using edge dataframe
        st.write(f"## Statistics for the graph retrieved")
        
        # Calculate basic statistics
        total_nodes = len(nodes)
        total_edges = len(edges)
        total_length = edges['length'].sum()
        avg_length = edges['length'].mean()
        


    
        edges["highway"] = edges.highway.map(lambda x: x[0] if isinstance(x, list) else x)

        edges["Groups"] = edges.highway

        edges["Groups"] = edges.highway.map(lambda x: 'C' if x  not in group3 else x)
        edges["Groups"] = edges.Groups.map(lambda x: 'A' if x  in group1 else x)
        edges["Groups"] = edges.Groups.map(lambda x: 'B' if x  in group2 else x)
        # Highway type distribution
        highway_counts = edges['highway'].value_counts()
        highway_percentages = (highway_counts / total_edges * 100).round(2)
        
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
        
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv().encode('utf-8')
    @st.fragment
    def download_data():
        csv_nodes = convert_df_to_csv(nodes.drop(columns=['geometry']))
        csv_edges = convert_df_to_csv(edges.drop(columns=['geometry']))
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download Nodes Data",
                data=csv_nodes,
                file_name=f'nodes_stats.csv',
                mime='text/csv',
            )
        with col2:
            st.download_button(
                label="Download Edges Data",
                data=csv_edges,
                file_name=f'edges_stats.csv',
                mime='text/csv',
            )
    download_data()