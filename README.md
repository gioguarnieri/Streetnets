# StreetNets

A no-code dashboard for retrieving, visualizing, and analyzing street networks from OpenStreetMap.

## Features

- **Home**: Landing page with an overview of the tool
- **Retrieve City Data**: Download and analyze the street network of any area (by point, geocoding, bounding box, drawn polygon, or uploaded shapefile)
- **City Database**: Explore pre-calculated statistics and maps for 18 example cities
- **Glossary**: Plain-language explanations of the technical terms used in the tool

## Installation

### As a package (recommended for users)

```bash
pip install .
streetnets
```

The `streetnets` command starts the app in your browser. On first use of the
City Database, the pre-analyzed city data (~27 MB) is downloaded automatically
into your user cache directory.

### From source (recommended for development)

```bash
pip install -r requirements.txt
streamlit run Home.py
```

A source checkout reads the city data directly from the `csv/` folder (or from
`data/` if you have generated the faster GeoParquet files, see below).

## How to Use

1. Use the sidebar (or the buttons on the home page) to navigate between pages
2. On the **Retrieve City Data** page, select an area and a network type, then click "Retrieve data" to view statistics, interactive maps, and download the data
3. On the **City Database** page, select a city to view its pre-calculated statistics and group maps

## Retrieve City Data Page

The Retrieve City Data page allows you to:

- Select an area by point + box size, geocoding query, bounding box, drawn polygon, or uploaded shapefile (.zip)
- View comprehensive statistics about the area's street network:
  - Basic network statistics (nodes, edges, total length)
  - Group distribution (A, B, C groups)
  - Highway type distribution
- Visualize the retrieved network on an interactive map
- Download the processed data in several formats (Shapefile, GeoJSON, Parquet, Feather, GPKG, SQLite, CSV)

## Data

The application retrieves live data from OpenStreetMap (via OSMnx) and ships
pre-calculated metrics from the [CoR GitHub repository](https://github.com/gioguarnieri/CoR/tree/main/Results/csv),
related to a paper in writing.

City files are searched in this order (see `streetnets_app/data.py`):

1. the directory named by the `STREETNETS_DATA` environment variable
2. `data/` (GeoParquet) and `csv/` (WKT CSVs) in a source checkout
3. the per-user cache, populated by downloading `streetnets_data.zip` from the
   project's GitHub release

### Maintainer notes

- `python scripts/convert_to_parquet.py` converts `csv/*.csv` to GeoParquet in
  `data/` (~6x smaller, much faster to load) and produces the content of the
  release bundle.
- To publish a new data bundle: zip the contents of `data/` as
  `streetnets_data.zip`, attach it to a GitHub release tagged `data-v1` (or bump
  `DATA_VERSION` in `streetnets_app/data.py`), and installed users will pick it
  up automatically.
- To build the package: `python -m build` (the wheel bundles `Home.py`, the
  `pages/`, and `examples_stats.csv`; the city data stays out of the wheel).

## Citing

The paper describing the methodology behind the street hierarchy groups and
the pre-calculated metrics is in preparation. Until it is published, please
cite this repository:

```
Guarnieri Soares, G. StreetNets: no-code street network analysis on
OpenStreetMap data. https://github.com/gioguarnieri/Streetnets
```

## Libraries Used

- streamlit: For creating the web application
- osmnx: For working with street networks
- geopandas: For geospatial data handling
- networkx: For network analysis
- plotly: For interactive visualizations
- folium / streamlit-folium: For interactive maps

Data © OpenStreetMap contributors.
