# Streetnets

A dashboard for visualizing and analyzing street networks from various cities.

## Features

- **Home**: Landing page with an overview of the tool
- **Retrieve City Data**: Download and analyze the street network of any area (by point, geocoding, bounding box, drawn polygon, or uploaded shapefile)
- **Database**: Explore pre-calculated statistics and maps for 18 example cities
- **Glossary**: Plain-language explanations of the technical terms used in the tool

## How to Use

1. Install the dependencies: `pip install -r requirements.txt`
2. Run the application with `streamlit run Home.py`
3. Use the sidebar (or the buttons on the home page) to navigate between pages
4. On the **Retrieve City Data** page, select an area and a network type, then click "Retrieve data" to view statistics, interactive maps, and download the data
5. On the **Database** page, select a city to view its pre-calculated statistics and group maps

## Retrieve City Data Page

The Retrieve City Data page allows you to:

- Select an area by point + box size, geocoding query, bounding box, drawn polygon, or uploaded shapefile (.zip)
- View comprehensive statistics about the area's street network:
  - Basic network statistics (nodes, edges, total length)
  - Group distribution (A, B, C groups)
  - Highway type distribution
- Visualize the retrieved network on an interactive map
- Download the processed data in several formats (Shapefile, GeoJSON, Parquet, Feather, GPKG, SQLite, CSV)

## Data Source

The application retrieves data from OpenStreetMap and pre-calculated metrics from the [CoR GitHub repository](https://github.com/gioguarnieri/CoR/tree/main/Results/csv), related to a paper in writing.

## Libraries Used

- streamlit: For creating the web application
- osmnx: For working with street networks
- geopandas: For geospatial data handling
- networkx: For network analysis
- plotly: For interactive visualizations
- folium / streamlit-folium: For interactive maps
