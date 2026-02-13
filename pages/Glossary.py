import streamlit as st

st.set_page_config(page_title="Glossary", page_icon="📖")

st.title("📖 Glossary of Terms")

st.markdown("This page explains the technical terms and settings used in the City Statistics tool in simple language.")

st.markdown("---")

st.header("1. Core Concepts")

st.markdown("""
### OpenStreetMap (OSM)
Think of **OpenStreetMap** as the "Wikipedia of Maps." It is a free, editable map of the whole world that is built by volunteers. 
Unlike Google Maps, the data in OSM is open-source, meaning anyone can download and analyze it. This tool uses OSM data to build the street networks you see.
""")

st.markdown("""
### OSMnx
**OSMnx** is the Python "engine" powering this tool. It allows us to download street data from OpenStreetMap and turn it into a mathematical structure called a **Graph**. 
Without OSMnx, downloading and cleaning up street maps for analysis would be incredibly difficult and require complex code.
""")

st.markdown("""
### Graph (Nodes and Edges)
In computer science, a "Graph" isn't a chart; it's a network of connected points. 
* **Node (Vertex):** These are the dots. In a street map, a Node is usually an **intersection** where roads meet, or a **dead-end** where a road stops.
* **Edge (Link):** These are the lines connecting the dots. An Edge represents the actual **street segment** or road between two intersections.
""")
st.write("") 

st.markdown("""
### GeoDataFrame
You might know what a spreadsheet or an Excel table is. A **GeoDataFrame** is just a super-powered spreadsheet for Python. 
It looks like a normal table with rows and columns, but it has a special "Geometry" column that stores the shape of the object (like a point for a Node or a line for a Street). This allows the computer to understand where the data sits on the Earth's surface.
""")

st.markdown("---")

st.header("2. Input Methods (How to select an area)")

st.markdown("""
These options determine *where* on the map we should retrieve data from.

* **📍 Point:** You pick a specific coordinate (Latitude/Longitude) and a distance (e.g., 1000 meters). The tool draws a circle around that point and grabs everything inside it.
* **🌍 Geocoding:** You type the name of a place (e.g., "New York, USA" or "Eiffel Tower"). The tool asks OpenStreetMap, "Where is this?" and retrieves the boundaries for that named place.
* **📦 From Bounding Box:** You provide the exact North, South, East, and West coordinates. This creates a rectangular box, and the tool grabs everything inside that rectangle.
* **✏️ Draw Polygon:** You manually draw a shape on the map. This is useful if you want a custom, irregular area that isn't a perfect circle or square.
* **📂 Shapefile:** You upload a professional map file (usually a `.zip` containing `.shp` files). This is common for government or official data boundaries.
""")

st.markdown("---")

st.header("3. Network Types (What kind of streets?)")

st.markdown("""
Not all streets are the same. A highway is great for cars but terrible for walking. You can filter the map by:

* **🚗 drive:** Standard drivable public streets. Excludes service roads (like alleyways).
* **🚛 drive_service:** Drivable public streets, *including* service roads.
* **🚶 walk:** All streets and paths that pedestrians can use (sidewalks, footpaths, crosswalks).
* **🚲 bike:** Streets and paths where cycling is allowed.
* **🌐 all:** All non-private streets and paths.
* **🔒 all_public:** All public streets (removes private driveways/access roads).
""")

st.markdown("---")

st.header("4. Statistics & Metrics")

st.markdown("""
### Circuity
**Circuity** measures how "direct" a route is. It compares the distance you *actually* have to travel versus the straight-line distance "as the crow flies."

* **Score of 1.0:** A perfectly straight line.
* **Score > 1.0:** The path is winding.
* **Example:** A winding mountain road has high circuity. A straight highway across a desert has low circuity.
""")
st.write("")

st.markdown("""
### Groups (Street Hierarchy)
We categorize streets into three groups based on how major they are (using OSM tags):

* **Group A (Highways):** Fast, major roads like motorways and trunks. Designed for high-speed traffic.
* **Group B (Arterial):** Main city streets like avenues and boulevards (Primary, Secondary, Tertiary).
* **Group C (Local):** Small residential streets, living streets, and unclassified roads.
""")
st.write("")