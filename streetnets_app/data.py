"""Data access for StreetNets.

City files are looked up in this order:

1. the directory named by the ``STREETNETS_DATA`` environment variable
2. the ``data/`` (GeoParquet) and ``csv/`` folders of a source checkout
3. ``csv/`` bundled inside the installed package (examples_stats.csv only)
4. the per-user cache directory, populated on first use by downloading the
   data bundle from the project's GitHub release

This module is Streamlit-free so it can be reused from scripts and tests;
the pages wrap the loaders in ``st.cache_data``.
"""

from __future__ import annotations

import os
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
import geopandas as gpd

DATA_VERSION = "v1"
DATA_URL = (
    "https://github.com/gioguarnieri/streetnets/releases/download/"
    f"data-{DATA_VERSION}/streetnets_data.zip"
)

PACKAGE_DIR = Path(__file__).resolve().parent

CITY_LIST = [
    "São Paulo",
    "Rio de Janeiro",
    "Atlanta",
    "Manhattan",
    "Barcelona",
    "Madrid",
    "Buenos Aires",
    "London",
    "Beijing",
    "Paris",
    "Cardiff",
    "Berlin",
    "Amsterdam",
    "São José dos Campos",
    "Los Angeles",
    "Wichita",
    "Toulouse",
    "Salt Lake",
]


def cache_dir() -> Path:
    from platformdirs import user_cache_dir

    return Path(user_cache_dir("streetnets")) / DATA_VERSION


def _search_dirs() -> list[Path]:
    dirs = []
    env = os.environ.get("STREETNETS_DATA")
    if env:
        dirs.append(Path(env))
    # Source checkout: the repo root is the parent of this package
    root = PACKAGE_DIR.parent
    dirs.append(root / "data")
    dirs.append(root / "csv")
    # Bundled inside the installed package
    dirs.append(PACKAGE_DIR / "csv")
    dirs.append(cache_dir())
    return dirs


def find_data_file(*names: str) -> Path | None:
    """Return the first existing path for any of ``names`` across search dirs."""
    for d in _search_dirs():
        for name in names:
            p = d / name
            if p.exists():
                return p
    return None


def download_data() -> Path:
    """Download and extract the data bundle into the user cache directory."""
    dest = cache_dir()
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "streetnets_data.zip"
    urllib.request.urlretrieve(DATA_URL, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    zip_path.unlink()
    return dest


def _resolve(*names: str) -> Path:
    path = find_data_file(*names)
    if path is None:
        download_data()
        path = find_data_file(*names)
    if path is None:
        raise FileNotFoundError(
            f"Could not find {' or '.join(names)} locally, and the downloaded "
            f"data bundle ({DATA_URL}) did not contain it."
        )
    return path


def load_city_edges(city: str, columns: list[str] | None = None) -> gpd.GeoDataFrame:
    """Load one pre-analyzed city's edges as a GeoDataFrame (EPSG:4326).

    Prefers GeoParquet; falls back to the WKT CSVs of a source checkout.
    ``columns`` must include ``geometry`` when given.
    """
    path = _resolve(f"{city}_edges.parquet", f"{city}_edges.csv")
    if path.suffix == ".parquet":
        return gpd.read_parquet(path, columns=columns)
    df = pd.read_csv(path, usecols=columns)
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkt(df["geometry"]),
        crs="epsg:4326",
    )


def load_city_nodes(city: str, columns: list[str] | None = None) -> gpd.GeoDataFrame:
    path = _resolve(f"{city}_nodes.parquet", f"{city}_nodes.csv")
    if path.suffix == ".parquet":
        return gpd.read_parquet(path, columns=columns)
    df = pd.read_csv(path, usecols=columns)
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkt(df["geometry"]),
        crs="epsg:4326",
    )


def load_examples_stats() -> pd.DataFrame:
    """Pre-calculated statistics for the example cities."""
    return pd.read_csv(_resolve("examples_stats.csv"), index_col=0)
