"""
ArcGIS Data Prep — Filter HIFLD shapefiles to 6 commuter rail agencies
========================================================================
Run this BEFORE uploading to ArcGIS Online.
Reduces file size and keeps the map clean.

Usage:
    pip install geopandas
    python prepare_shapefiles.py \
        --lines  path/to/north_american_rail_lines.zip \
        --stations path/to/passenger_rail_stations.zip

Outputs (saved to /arcgis_data/):
    rail_lines_filtered.zip      ← upload to ArcGIS as hosted feature layer
    stations_filtered.zip        ← upload to ArcGIS as hosted feature layer
    kpi_join_table.csv           ← upload to ArcGIS as table for join

The script also prints every unique operator name it finds in the
HIFLD files so you can verify the filter strings match exactly.
"""

import argparse
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd

# ── Your 6 agencies — edit these strings if HIFLD uses different names ────────
AGENCY_FILTERS = {
    "MBTA":       ["Massachusetts Bay Transportation", "MBTA", "Keolis"],
    "NJ Transit": ["NJ TRANSIT", "New Jersey Transit", "NJ Transit"],
    "SEPTA":      ["SEPTA", "Southeastern Pennsylvania"],
    "MARC":       ["MARC", "Maryland Area Regional Commuter",
                   "Maryland Transit Administration"],
    "Metra":      ["Metra", "Northeast Illinois Regional",
                   "BNSF Railway", "Union Pacific"],  # Metra uses freight ROW
    "Caltrain":   ["Caltrain", "Peninsula Corridor", "JPB"],
}

# KPI data from your analysis
KPI_DATA = {
    "MBTA":       {"otp": 0.9315, "composite_score": 69.9, "cost_per_trip": 20.33,
                   "ridership_density": 56614, "fleet_utilization": 0.849},
    "NJ Transit": {"otp": 0.921,  "composite_score": 53.5, "cost_per_trip": 24.46,
                   "ridership_density": 53231, "fleet_utilization": 0.663},
    "SEPTA":      {"otp": 0.879,  "composite_score": 55.3, "cost_per_trip": 16.56,
                   "ridership_density": 68227, "fleet_utilization": 0.745},
    "MARC":       {"otp": 0.900,  "composite_score": 10.9, "cost_per_trip": 46.88,
                   "ridership_density": 18058, "fleet_utilization": 0.741},
    "Metra":      {"otp": 0.950,  "composite_score": 29.2, "cost_per_trip": 28.03,
                   "ridership_density": 28060, "fleet_utilization": 0.618},
    "Caltrain":   {"otp": 0.920,  "composite_score": 76.8, "cost_per_trip": 24.66,
                   "ridership_density": 91066, "fleet_utilization": 0.639},
}

OTP_TIER = {
    "MBTA":       "High",
    "NJ Transit": "High",
    "SEPTA":      "Low",
    "MARC":       "Medium",
    "Metra":      "High",
    "Caltrain":   "High",
}


def match_agency(value: str) -> str | None:
    """Return the canonical agency name if value matches any filter string."""
    if not isinstance(value, str):
        return None
    val_upper = value.upper()
    for agency, keywords in AGENCY_FILTERS.items():
        for kw in keywords:
            if kw.upper() in val_upper:
                return agency
    return None


def filter_lines(lines_path: str, out_dir: str) -> str:
    print(f"\n── Rail lines: {lines_path}")
    gdf = gpd.read_file(lines_path)
    print(f"   Total features: {len(gdf):,}")
    print(f"   Columns: {list(gdf.columns)}")

    # Print unique operator values to help with filter matching
    op_cols = [c for c in gdf.columns if any(
        k in c.upper() for k in ["OPER", "OWNER", "RR", "RAIL", "NAME", "AGENCY"]
    )]
    print(f"   Candidate operator columns: {op_cols}")
    for col in op_cols[:3]:
        print(f"   Unique {col} values (sample): {gdf[col].dropna().unique()[:15].tolist()}")

    # Try to match against best operator column
    matched = gpd.GeoDataFrame()
    for col in op_cols:
        gdf["_agency"] = gdf[col].apply(match_agency)
        subset = gdf[gdf["_agency"].notna()].copy()
        if len(subset) > matched.__len__():
            matched = subset
            best_col = col

    if len(matched) == 0:
        print("   WARNING: No matches found. Check AGENCY_FILTERS strings against the")
        print("   operator column values printed above and edit the script.")
        return None

    print(f"   Matched {len(matched):,} features across {matched['_agency'].nunique()} agencies")
    print(f"   Match counts: {matched['_agency'].value_counts().to_dict()}")

    # Add KPI columns for choropleth styling
    for kpi in ["otp", "composite_score", "cost_per_trip", "ridership_density"]:
        matched[kpi] = matched["_agency"].map({k: v[kpi] for k, v in KPI_DATA.items()})

    matched["otp_tier"]  = matched["_agency"].map(OTP_TIER)
    matched["otp_pct"]   = (matched["otp"] * 100).round(1)
    matched["agency"]    = matched["_agency"]
    matched = matched.drop(columns=["_agency"])

    # Reproject to WGS84 for ArcGIS Online
    matched = matched.to_crs("EPSG:4326")

    out_shp = os.path.join(out_dir, "rail_lines_filtered.shp")
    matched.to_file(out_shp)

    out_zip = os.path.join(out_dir, "rail_lines_filtered.zip")
    _zip_shapefile(out_dir, "rail_lines_filtered", out_zip)
    print(f"   Saved: {out_zip}")
    return out_zip


def filter_stations(stations_path: str, out_dir: str) -> str:
    print(f"\n── Stations: {stations_path}")
    gdf = gpd.read_file(stations_path)
    print(f"   Total features: {len(gdf):,}")
    print(f"   Columns: {list(gdf.columns)}")

    op_cols = [c for c in gdf.columns if any(
        k in c.upper() for k in ["OPER", "OWNER", "RR", "RAIL", "NAME", "AGENCY", "SYSNAME"]
    )]
    print(f"   Candidate operator columns: {op_cols}")
    for col in op_cols[:3]:
        print(f"   Unique {col} values (sample): {gdf[col].dropna().unique()[:15].tolist()}")

    matched = gpd.GeoDataFrame()
    for col in op_cols:
        gdf["_agency"] = gdf[col].apply(match_agency)
        subset = gdf[gdf["_agency"].notna()].copy()
        if len(subset) > matched.__len__():
            matched = subset

    if len(matched) == 0:
        print("   WARNING: No matches found for stations.")
        return None

    print(f"   Matched {len(matched):,} stations")
    print(f"   By agency: {matched['_agency'].value_counts().to_dict()}")

    # Add KPI columns for pop-up display
    matched["agency"] = matched["_agency"]
    for kpi in ["otp", "composite_score", "cost_per_trip"]:
        matched[kpi] = matched["_agency"].map({k: v[kpi] for k, v in KPI_DATA.items()})
    matched["otp_pct"] = (matched["otp"] * 100).round(1)
    matched = matched.drop(columns=["_agency"])
    matched = matched.to_crs("EPSG:4326")

    out_shp = os.path.join(out_dir, "stations_filtered.shp")
    matched.to_file(out_shp)

    out_zip = os.path.join(out_dir, "stations_filtered.zip")
    _zip_shapefile(out_dir, "stations_filtered", out_zip)
    print(f"   Saved: {out_zip}")
    return out_zip


def build_kpi_table(out_dir: str) -> str:
    """Build the KPI join table — upload this to ArcGIS as a CSV table."""
    rows = []
    for agency, kpis in KPI_DATA.items():
        row = {"agency": agency}
        row.update(kpis)
        row["otp_pct"] = round(kpis["otp"] * 100, 1)
        row["otp_tier"] = OTP_TIER[agency]
        rows.append(row)

    df = pd.DataFrame(rows)
    out = os.path.join(out_dir, "kpi_join_table.csv")
    df.to_csv(out, index=False)
    print(f"\n── KPI join table saved: {out}")
    return out


def _zip_shapefile(directory: str, stem: str, out_zip: str):
    """Zip all files with the given stem into a single .zip."""
    exts = [".shp", ".shx", ".dbf", ".prj", ".cpg"]
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for ext in exts:
            fp = os.path.join(directory, stem + ext)
            if os.path.exists(fp):
                zf.write(fp, os.path.basename(fp))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lines",    required=True,
                        help="Path to HIFLD rail lines .zip or .shp")
    parser.add_argument("--stations", required=True,
                        help="Path to HIFLD passenger stations .zip or .shp")
    parser.add_argument("--out",      default="arcgis_data",
                        help="Output directory (default: arcgis_data/)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    filter_lines(args.lines, args.out)
    filter_stations(args.stations, args.out)
    build_kpi_table(args.out)

    print(f"\n✓ All done. Upload these 3 files to ArcGIS Online:")
    print(f"   {args.out}/rail_lines_filtered.zip  → hosted feature layer")
    print(f"   {args.out}/stations_filtered.zip     → hosted feature layer")
    print(f"   {args.out}/kpi_join_table.csv        → table item (for join)")


if __name__ == "__main__":
    main()
