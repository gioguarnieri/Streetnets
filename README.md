README

# Streetnets

A dashboard for visualizing and analyzing street networks from various cities.

## Features

- **Main Dashboard**: Visualize city street networks with different metrics
- **Stats Page**: View statistical visualizations of street network data
- **City Statistics Page**: Calculate and display comprehensive statistics for any city

## How to Use

1. Run the application with `streamlit run main.py`
2. Use the sidebar to navigate between different pages
3. On the main page, select a city to visualize its street network
4. On the Stats page, view statistical visualizations of the selected city
5. On the City Statistics page, either select a city from the list or enter a custom city name to view detailed statistics

## City Statistics Page

The new City Statistics page allows you to:

- Select a city from the predefined list or enter a custom city name
- View comprehensive statistics about the city's street network:
  - Basic network statistics (nodes, edges, total length)
  - Group distribution (A, B, C groups)
  - Highway type distribution
  - Detailed metrics for Inverse SP, Cost of Return, and Edge Betweenness
- Visualize data with interactive charts
- Download the processed data as CSV files

## Data Source

The application retrieves data from OpenStreetMap and pre-calculated metrics from the [CoR GitHub repository](https://github.com/gioguarnieri/CoR/tree/main/Results/csv), related to a paper in writing.

## Libraries Used

- streamlit: For creating the web application
- osmnx: For working with street networks
- geopandas: For geospatial data handling
- networkx: For network analysis
- plotly: For interactive visualizations
