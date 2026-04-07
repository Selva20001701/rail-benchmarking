# ArcGIS Online — Setup Guide

## What you're building
A public web map with 4 layers:
1. **Rail lines** — styled by OTP % (green → amber → red choropleth)
2. **Station points** — color-coded by agency, pop-ups with KPI data
3. **Walkshed isochrones** — 10-min and 20-min walking catchments around stations
4. **Population density** — Living Atlas underlay showing who lives near each system

Published URL goes into the GitHub README as the hero link.

---

## Step 0 — Prep (run before opening ArcGIS)

```bash
pip install geopandas
python arcgis/prepare_shapefiles.py \
    --lines   path/to/north_american_rail_lines.zip \
    --stations path/to/passenger_rail_stations.zip
```

**Downloads needed:**
- Rail lines: `hifld-geoplatform.opendata.arcgis.com` → search "railroad" → "North American Rail Lines" → Shapefile
- Stations: same site → search "passenger rail stations" → Shapefile

Script outputs to `arcgis_data/`:
- `rail_lines_filtered.zip` — 6 agencies only, KPI fields attached
- `stations_filtered.zip` — 6 agencies only, KPI fields attached
- `kpi_join_table.csv` — agency-level KPIs for the join

---

## Step 1 — Upload to ArcGIS Online (~20 min)

1. Sign in → **Content** → **New Item** → **Your device**
2. Upload `rail_lines_filtered.zip` → "Add and create a hosted feature layer" → Finish
3. Repeat for `stations_filtered.zip`
4. Upload `kpi_join_table.csv` as a table item

---

## Step 2 — Build the map (~30 min)

1. Open rail lines layer → **Open in Map Viewer**
2. Add layers → My content → add stations layer
3. Style rail lines: **Styles** → field = `otp_pct` → Counts and Amounts (Color)
   - Color ramp: `#276221` (high OTP) → `#9C6500` (mid) → `#9C0006` (low)
4. Style stations: Styles → field = `agency` → Unique Values → assign colors matching your Python charts
5. Add Living Atlas: Add layer → Living Atlas → "USA Population Density" → opacity 40%
6. Add layer → **Analysis** → **Use Proximity** → **Create Drive-Time Areas**
   - Input = stations layer
   - Measurement type = Walking time
   - Break values = 10, 20
   - Run (uses ~100 credits)

---

## Step 3 — Publish

1. Save map → title: "U.S. Commuter Rail Benchmarking — FY2023"
2. Share → Everyone (public)
3. Copy the URL
4. Export a screenshot (full map, all layers visible)
5. Add to README:
   ```markdown
   🗺️ **[View Interactive ArcGIS Map →](YOUR_URL_HERE)**
   ![Map screenshot](outputs/arcgis_screenshot.png)
   ```

---

## Credit estimate

| Operation | Credits |
|---|---|
| Upload hosted feature layers | 0 |
| Service Area (walkshed) ~200 stations × 2 breaks | ~200 |
| Map views (public) | 0 |

If low on credits, run isochrones for MBTA only as a demonstration (~20 credits).
