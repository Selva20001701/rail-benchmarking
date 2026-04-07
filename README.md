# U.S. Commuter Rail Benchmarking Dashboard — FY2023

> Comparative analysis of 6 U.S. commuter rail systems across 6 key performance indicators,
> with spatial visualization in ArcGIS Online and a weighted composite scoring model.

🗺️ **[View Interactive ArcGIS Map →](https://arcg.is/1jry0n5)** 

---

## Systems Analyzed

| Agency | Region | NTD ID |
|--------|--------|--------|
| MBTA | Northeast | 10001 |
| NJ Transit | Northeast | 20215 |
| SEPTA | Mid-Atlantic | 30030 |
| Metra | Midwest | 50077 |
| Caltrain | West Coast | 90026 |
| MARC | Mid-Atlantic | 30034 |

---

## Key Findings

*(Update after entering real data — auto-generated from notebook Section 5)*

1. **[Top Agency]** ranks first overall with a composite score of **[X]**, driven by the highest ridership density in the dataset at **[X] trips/route mile**.
2. **Cost efficiency** varies widely across systems — a **$[X] spread** in operating cost per trip suggests significant differences in fleet age, labor agreements, and network density.
3. **On-time performance** correlates with **[finding from correlation matrix]**, suggesting infrastructure investment in signaling and track would yield the highest reliability returns.
4. **Northeast corridor systems** (MBTA, NJ Transit) serve denser populations within smaller route mile footprints, resulting in higher ridership density despite similar fleet sizes.

---

## Methodology

### KPIs Computed

| KPI | Formula | Weight in Composite | Better Direction |
|-----|---------|---------------------|-----------------|
| Ridership Density | UPT ÷ Route Miles | 25% | ↑ Higher |
| Cost Efficiency | OpEx ÷ UPT | 20% | ↓ Lower |
| Fleet Utilization | VOMS ÷ VAMS | 15% | ↑ Higher |
| Service Intensity | VRM ÷ Route Miles | 15% | ↑ Higher |
| Rev. Hr Efficiency | UPT ÷ VRH | 15% | ↑ Higher |
| On-Time Performance | Agency-reported | 10% | ↑ Higher |

### Composite Score
Each KPI is normalized min-max to 0–100 across the 6 systems, then multiplied by its weight. Cost per trip is inverted so that lower cost = higher normalized score.

### Data Sources
- **NTD FY2023 Metrics CSV** — `data.transportation.gov/Public-Transit/2022-2024-NTD-Annual-Data-Metrics/ekg5-frzt`
- **NTD FY2023 Agency Mode Service** — `transit.dot.gov/ntd/data-product/2023-annual-database-agency-mode-service`
- **Agency OTP Dashboards** — individual agency performance portals (see `data/raw_data.csv` source comments)

---

## Outputs

| File | Description |
|------|-------------|
| `outputs/fig1_composite_score.png` | Overall ranking bar chart |
| `outputs/fig2_kpi_rankings_heatmap.png` | KPI rank heatmap across all agencies |
| `outputs/fig3_correlation_heatmap.png` | Pearson correlation matrix |
| `outputs/fig4_cost_vs_otp.png` | Cost efficiency vs OTP scatter (bubble = ridership) |
| `outputs/fig5_ridership_density.png` | Ridership density by agency and region |
| `outputs/fig6_radar_chart.png` | Normalized KPI profile radar chart |
| `outputs/summary_kpis.csv` | Full KPI table, exportable |
| `data/rail_benchmarking_sheets.xlsx` | Excel/Sheets workbook with live formulas |

---

## How to Run

```bash
# Clone and install
git clone https://github.com/[your-username]/rail-benchmarking
cd rail-benchmarking
pip install -r requirements.txt

# Run full analysis (generates all figures)
python analysis/benchmark_analysis.py

# Or with custom data path
python analysis/benchmark_analysis.py --data data/raw_data.csv

# Open the notebook for step-by-step walkthrough
jupyter notebook notebooks/exploration.ipynb
```

---

## Repo Structure

```
rail-benchmarking/
├── analysis/
│   └── benchmark_analysis.py   # Main analysis script
├── notebooks/
│   └── exploration.ipynb       # Step-by-step walkthrough
├── data/
│   ├── raw_data.csv            # Compiled FY2023 data (NTD + agency)
│   └── rail_benchmarking_sheets.xlsx  # Excel/Sheets workbook
├── outputs/                    # All generated figures (300 dpi)
├── reports/                    # Technical brief PDF
└── requirements.txt
```

---
