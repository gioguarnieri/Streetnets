"""Convert the bundled city CSVs (WKT geometry) to GeoParquet.

Reads csv/<City>_{edges,nodes}.csv and writes data/<City>_{edges,nodes}.parquet
with all columns preserved. GeoParquet files are ~5-10x smaller and load much
faster than WKT-in-CSV. Also copies examples_stats.csv into data/ so the data/
folder is a complete, self-contained bundle for the GitHub release.

Usage: python scripts/convert_to_parquet.py
"""

import shutil
import sys
import time
from pathlib import Path

import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from streetnets_app.data import CITY_LIST  # noqa: E402

CSV_DIR = ROOT / "csv"
OUT_DIR = ROOT / "data"


def convert(csv_path: Path, out_path: Path) -> None:
    df = pd.read_csv(csv_path)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkt(df["geometry"]),
        crs="epsg:4326",
    )
    gdf.to_parquet(out_path, index=False)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    total_before = total_after = 0
    for city in CITY_LIST:
        for kind in ("edges", "nodes"):
            src = CSV_DIR / f"{city}_{kind}.csv"
            dst = OUT_DIR / f"{city}_{kind}.parquet"
            t0 = time.time()
            convert(src, dst)
            total_before += src.stat().st_size
            total_after += dst.stat().st_size
            print(f"{src.name}: {src.stat().st_size/1e6:.1f} MB -> "
                  f"{dst.stat().st_size/1e6:.1f} MB ({time.time()-t0:.1f}s)")
    shutil.copy(CSV_DIR / "examples_stats.csv", OUT_DIR / "examples_stats.csv")
    print(f"\nTotal: {total_before/1e6:.0f} MB -> {total_after/1e6:.0f} MB")


if __name__ == "__main__":
    main()
