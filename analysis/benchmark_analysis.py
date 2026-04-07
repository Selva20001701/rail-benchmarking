"""
U.S. Commuter Rail Benchmarking Analysis
=========================================
Loads FY2023 data for 6 commuter rail systems, computes KPIs,
and generates all figures for the GitHub README and technical brief.

Outputs (saved to /outputs):
    fig1_composite_score.png       - Horizontal bar chart, overall ranking
    fig2_kpi_rankings.png          - Grouped bar chart, all KPI ranks
    fig3_correlation_heatmap.png   - Pearson correlation matrix of KPIs
    fig4_cost_vs_otp.png           - Scatter: cost/trip vs on-time performance
    fig5_ridership_density.png     - Bar: ridership density by agency + region
    fig6_radar_chart.png           - Radar/spider chart, normalized KPI profiles

Usage:
    python analysis/benchmark_analysis.py
    python analysis/benchmark_analysis.py --data data/raw_data.csv
"""

import argparse
import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
from matplotlib.patches import FancyBboxPatch
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

# ── Config ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")

PALETTE = {
    "navy":       "#1F3864",
    "steel":      "#2E5F8A",
    "light_blue": "#D6E4F0",
    "pale_blue":  "#EBF4FA",
    "white":      "#FFFFFF",
    "dark_gray":  "#404040",
    "mid_gray":   "#808080",
    "green":      "#276221",
    "amber":      "#9C6500",
    "red":        "#9C0006",
}

AGENCY_COLORS = {
    "MBTA":       "#1F3864",
    "NJ Transit": "#2E5F8A",
    "SEPTA":      "#4A7FB5",
    "Metra":      "#276221",
    "Caltrain":   "#9C6500",
    "MARC":       "#6B3FA0",
}

REGION_COLORS = {
    "Northeast":    "#2E5F8A",
    "Mid-Atlantic": "#276221",
    "Midwest":      "#9C6500",
    "West Coast":   "#6B3FA0",
}

plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   True,
    "axes.spines.bottom": True,
    "axes.grid":          True,
    "grid.color":         "#E8E8E8",
    "grid.linewidth":     0.6,
    "axes.titlesize":     13,
    "axes.titleweight":   "bold",
    "axes.titlecolor":    "#1F3864",
    "axes.labelsize":     10,
    "axes.labelcolor":    "#404040",
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "figure.facecolor":   "white",
    "axes.facecolor":     "white",
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
    "savefig.facecolor":  "white",
})

WEIGHTS = {
    "ridership_density":    0.25,
    "fleet_utilization":    0.15,
    "cost_per_trip":        0.20,   # inverted
    "service_intensity":    0.15,
    "rev_hr_efficiency":    0.15,
    "otp":                  0.10,
}

# ── Data Loading & KPI Computation ────────────────────────────────────────────
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["ridership_density"]  = d["upt"] / d["route_miles"]
    d["fleet_utilization"]  = d["voms"] / d["vams"]
    d["cost_per_trip"]      = d["opex_usd"] / d["upt"]
    d["service_intensity"]  = d["vrm"] / d["route_miles"]
    d["rev_hr_efficiency"]  = d["upt"] / d["vrh"]
    d["peak_capacity"]      = d["peak_trains_per_dir"] * d["avg_train_seats"]

    # Normalize each KPI to 0–100 (min-max), cost is inverted
    kpis = list(WEIGHTS.keys())
    for kpi in kpis:
        mn, mx = d[kpi].min(), d[kpi].max()
        if mx == mn:
            d[f"{kpi}_norm"] = 50.0
        elif kpi == "cost_per_trip":
            d[f"{kpi}_norm"] = (1 - (d[kpi] - mn) / (mx - mn)) * 100
        else:
            d[f"{kpi}_norm"] = ((d[kpi] - mn) / (mx - mn)) * 100

    # Weighted composite score
    d["composite_score"] = sum(
        d[f"{kpi}_norm"] * w for kpi, w in WEIGHTS.items()
    ).round(1)

    # Overall rank
    d["overall_rank"] = d["composite_score"].rank(ascending=False).astype(int)

    # Tier
    def tier(score):
        if score >= 75: return "Top Performer"
        if score >= 50: return "Average"
        if score >= 25: return "Below Average"
        return "Needs Improvement"
    d["tier"] = d["composite_score"].apply(tier)

    return d.sort_values("composite_score", ascending=False).reset_index(drop=True)


def add_footnote(fig, text):
    fig.text(0.01, 0.005, text,
             fontsize=7, color=PALETTE["mid_gray"],
             ha="left", va="bottom", style="italic")


# ── Figure 1: Composite Score Ranking ─────────────────────────────────────────
def fig_composite_score(df: pd.DataFrame, out_dir: str):
    fig, ax = plt.subplots(figsize=(10, 5.5))

    colors = [AGENCY_COLORS[a] for a in df["agency"]]
    bars = ax.barh(df["agency"], df["composite_score"],
                   color=colors, height=0.55, zorder=3)

    # Value labels
    for bar, score, tier in zip(bars, df["composite_score"], df["tier"]):
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                f"{score:.1f}  [{tier}]",
                va="center", ha="left", fontsize=9, color=PALETTE["dark_gray"])

    ax.set_xlim(0, 115)
    ax.set_xlabel("Composite Score (0–100)", fontsize=10)
    ax.set_title("FY2023 Overall Composite Score — U.S. Commuter Rail Systems",
                 pad=14)
    ax.invert_yaxis()
    ax.axvline(50, color=PALETTE["mid_gray"], linestyle="--",
               linewidth=0.8, zorder=2, label="Average threshold (50)")
    ax.legend(fontsize=8, framealpha=0.7)

    # Subtitle
    fig.text(0.13, 0.93,
             "Weighted across 6 KPIs: Ridership Density (25%), Cost Efficiency (20%), "
             "Fleet Utilization (15%), Service Intensity (15%), Rev. Hr Efficiency (15%), OTP (10%)",
             fontsize=8, color=PALETTE["mid_gray"], ha="left")

    add_footnote(fig, "Source: NTD FY2023 Annual Data & Agency Performance Dashboards  |  "
                       "Analysis: U.S. Commuter Rail Benchmarking Project")
    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    fig.savefig(os.path.join(out_dir, "fig1_composite_score.png"))
    plt.close(fig)
    print("  ✓  fig1_composite_score.png")


# ── Figure 2: KPI Rankings Heatmap ────────────────────────────────────────────
def fig_kpi_rankings(df: pd.DataFrame, out_dir: str):
    from matplotlib.colors import LinearSegmentedColormap

    kpi_labels = {
        "ridership_density": "Ridership\nDensity",
        "fleet_utilization": "Fleet\nUtilization",
        "cost_per_trip":     "Cost/Trip\n(inverted)",
        "service_intensity": "Service\nIntensity",
        "rev_hr_efficiency": "Rev. Hr\nEfficiency",
        "otp":               "On-Time\nPerf.",
    }

    # Use .values to strip pandas integer index — prevents NaN from index mismatch
    rank_data = {}
    for kpi, label in kpi_labels.items():
        if kpi == "cost_per_trip":
            rank_data[label] = df[kpi].rank(ascending=True).values.astype(int)
        else:
            rank_data[label] = df[kpi].rank(ascending=False).values.astype(int)

    rank_df = pd.DataFrame(rank_data, index=df["agency"].values)

    fig, ax = plt.subplots(figsize=(13, 5.5))

    # Green (rank 1) → Yellow → Red (rank 6)
    cmap = LinearSegmentedColormap.from_list(
        "rank", ["#C6EFCE", "#FFEB9C", "#FFC7CE"][::-1], N=256
    )
    mat = rank_df.values.astype(float)
    im  = ax.imshow(mat, cmap=cmap, vmin=1, vmax=6, aspect="auto")

    # Annotate each cell
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = int(mat[i, j])
            if val == 1:
                clr, wt = "#276221", "bold"
            elif val == 6:
                clr, wt = "#9C0006", "bold"
            else:
                clr, wt = "#404040", "normal"
            ax.text(j, i, str(val), ha="center", va="center",
                    fontsize=15, fontweight=wt, color=clr)

    ax.set_xticks(range(len(rank_df.columns)))
    ax.set_xticklabels(rank_df.columns, fontsize=10, ha="center", linespacing=1.3)
    ax.set_yticks(range(len(rank_df.index)))
    ax.set_yticklabels(rank_df.index, fontsize=11)
    ax.tick_params(length=0)

    # White grid between cells
    ax.set_xticks(np.arange(-0.5, len(rank_df.columns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rank_df.index),   1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2.5)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.grid(which="major", visible=False)
    ax.spines[:].set_visible(False)

    cbar = plt.colorbar(im, ax=ax, shrink=0.75, aspect=18, pad=0.02)
    cbar.set_label("Rank  (1 = Best,  6 = Worst)", fontsize=9)
    cbar.set_ticks([1, 2, 3, 4, 5, 6])
    cbar.ax.tick_params(labelsize=9)

    ax.set_title("FY2023 KPI Rankings by Agency — U.S. Commuter Rail Systems", pad=14)

    add_footnote(fig, "Source: NTD FY2023  |  Green bold = Rank 1 (best), Red bold = Rank 6 (worst)  |  Cost/Trip inverted: lower cost = Rank 1")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(os.path.join(out_dir, "fig2_kpi_rankings_heatmap.png"))
    plt.close(fig)
    print("  ✓  fig2_kpi_rankings_heatmap.png")


# ── Figure 3: Correlation Heatmap ─────────────────────────────────────────────
def fig_correlation(df: pd.DataFrame, out_dir: str):
    kpi_cols = list(WEIGHTS.keys()) + ["composite_score", "peak_capacity"]
    labels   = ["Ridership\nDensity", "Fleet\nUtil.", "Cost/Trip",
                 "Svc\nIntensity", "Rev. Hr\nEff.", "OTP",
                 "Composite\nScore", "Peak\nCapacity"]

    corr = df[kpi_cols].corr(method="pearson")
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)

    fig, ax = plt.subplots(figsize=(9, 7))
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=1, vmin=-1, center=0,
                square=True, linewidths=0.5, linecolor="#E0E0E0",
                annot=True, fmt=".2f", annot_kws={"size": 9},
                xticklabels=labels, yticklabels=labels,
                cbar_kws={"shrink": 0.7, "label": "Pearson r"},
                ax=ax)

    ax.set_title("KPI Correlation Matrix — U.S. Commuter Rail Systems (FY2023)", pad=14)
    ax.tick_params(axis="x", labelsize=8.5, rotation=0)
    ax.tick_params(axis="y", labelsize=8.5, rotation=0)

    add_footnote(fig, "Pearson correlation coefficient  |  Lower triangle only  |  "
                       "Strong positive = dark blue, strong negative = dark red")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(os.path.join(out_dir, "fig3_correlation_heatmap.png"))
    plt.close(fig)
    print("  ✓  fig3_correlation_heatmap.png")


# ── Figure 4: Cost vs OTP Scatter ─────────────────────────────────────────────
def fig_cost_vs_otp(df: pd.DataFrame, out_dir: str):
    fig, ax = plt.subplots(figsize=(10, 6.5))

    for _, row in df.iterrows():
        color = AGENCY_COLORS[row["agency"]]
        ax.scatter(row["cost_per_trip"], row["otp"] * 100,
                   s=row["upt"] / 400_000,
                   color=color, alpha=0.85, zorder=4,
                   edgecolors="white", linewidths=1.5)
        offsets = {
            "MBTA":       (8,   4),
            "NJ Transit": (8,   4),
            "SEPTA":      (8, -10),
            "MARC":       (-62,  6),
            "Metra":      (8,   4),
            "Caltrain":   (8,   4),
        }
        ox, oy = offsets.get(row["agency"], (8, 4))
        ax.annotate(row["agency"],
                    (row["cost_per_trip"], row["otp"] * 100),
                    textcoords="offset points", xytext=(ox, oy),
                    fontsize=10, color=color, fontweight="bold")

    x = df["cost_per_trip"]
    y = df["otp"] * 100
    if len(x) > 2:
        slope, intercept, r, p, _ = stats.linregress(x, y)
        x_line = np.linspace(x.min() * 0.85, x.max() * 1.05, 200)
        ax.plot(x_line, slope * x_line + intercept,
                "--", color=PALETTE["mid_gray"], linewidth=1.2,
                label=f"Trend  (r = {r:.2f}, p = {p:.2f})", zorder=3)
        ax.legend(fontsize=9, framealpha=0.8)

    # Ensure full x-axis range including MARC outlier
    ax.set_xlim(x.min() * 0.82, x.max() * 1.12)
    ax.set_ylim(y.min() - 0.6, y.max() + 0.6)
    ax.set_xlabel("Operating Cost per Trip (USD)", fontsize=11)
    ax.set_ylabel("On-Time Performance (%)", fontsize=11)
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.1f%%"))
    ax.xaxis.set_major_formatter(mtick.FormatStrFormatter("$%.0f"))
    ax.set_title("Cost Efficiency vs. On-Time Performance — FY2023\n"
                 "(Bubble size = annual ridership)", pad=14)

    xm, ym = x.mean(), y.mean()
    ax.axvline(xm, color="#D0D0D0", linewidth=0.8, linestyle=":")
    ax.axhline(ym, color="#D0D0D0", linewidth=0.8, linestyle=":")
    ax.text(x.min() * 0.84, ym + 0.08, "Low Cost\nHigh OTP\n✓ Ideal",
            fontsize=8, color=PALETTE["green"], alpha=0.9, va="bottom")
    ax.text(x.max() * 1.01, ym - 0.3, "High Cost\nLow OTP",
            fontsize=8, color=PALETTE["red"], alpha=0.9, va="top", ha="left")

    add_footnote(fig, "Source: NTD FY2023  |  OTP from agency dashboards  |  "
                       "Bubble size proportional to annual unlinked passenger trips")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(os.path.join(out_dir, "fig4_cost_vs_otp.png"))
    plt.close(fig)
    print("  ✓  fig4_cost_vs_otp.png")


# ── Figure 5: Ridership Density ────────────────────────────────────────────────
def fig_ridership_density(df: pd.DataFrame, out_dir: str):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5),
                              gridspec_kw={"width_ratios": [2, 1]})

    # Left — bar chart by agency
    ax = axes[0]
    sorted_df = df.sort_values("ridership_density", ascending=True)
    colors = [AGENCY_COLORS[a] for a in sorted_df["agency"]]
    bars = ax.barh(sorted_df["agency"], sorted_df["ridership_density"],
                   color=colors, height=0.55, zorder=3)
    for bar, val in zip(bars, sorted_df["ridership_density"]):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", va="center", fontsize=9,
                color=PALETTE["dark_gray"])
    ax.set_xlabel("Unlinked Passenger Trips per Route Mile", fontsize=10)
    ax.set_title("Ridership Density by Agency", pad=10)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(
        lambda x, _: f"{x/1000:.0f}k" if x >= 1000 else f"{x:.0f}"))

    # Right — by region (grouped)
    ax2 = axes[1]
    region_avg = df.groupby("region")["ridership_density"].mean().sort_values(ascending=True)
    region_cols = [REGION_COLORS.get(r, PALETTE["steel"]) for r in region_avg.index]
    ax2.barh(region_avg.index, region_avg.values,
             color=region_cols, height=0.5, zorder=3)
    for i, (region, val) in enumerate(region_avg.items()):
        ax2.text(val + 200, i, f"{val:,.0f}", va="center",
                 fontsize=9, color=PALETTE["dark_gray"])
    ax2.set_xlabel("Avg Trips per Route Mile", fontsize=10)
    ax2.set_title("By Region\n(avg)", pad=10)
    ax2.xaxis.set_major_formatter(mtick.FuncFormatter(
        lambda x, _: f"{x/1000:.0f}k" if x >= 1000 else f"{x:.0f}"))

    fig.suptitle("FY2023 Ridership Density — U.S. Commuter Rail Systems",
                 fontsize=13, fontweight="bold", color=PALETTE["navy"], y=1.01)
    add_footnote(fig, "Source: NTD FY2023  |  Ridership Density = Annual UPT ÷ Directional Route Miles")
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(os.path.join(out_dir, "fig5_ridership_density.png"))
    plt.close(fig)
    print("  ✓  fig5_ridership_density.png")


# ── Figure 6: Radar Chart ──────────────────────────────────────────────────────
def fig_radar(df: pd.DataFrame, out_dir: str):
    kpis = list(WEIGHTS.keys())
    labels = ["Ridership\nDensity", "Fleet\nUtil.", "Cost\nEfficiency",
              "Svc\nIntensity", "Rev. Hr\nEff.", "OTP"]
    n = len(kpis)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=9.5, color=PALETTE["dark_gray"])
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"],
                        size=7, color=PALETTE["mid_gray"])
    ax.grid(color="#E0E0E0", linewidth=0.7)
    ax.spines["polar"].set_visible(False)

    for _, row in df.iterrows():
        vals = [row[f"{k}_norm"] for k in kpis]
        vals += vals[:1]
        color = AGENCY_COLORS[row["agency"]]
        ax.plot(angles, vals, "o-", linewidth=1.8, color=color,
                markersize=4, label=row["agency"])
        ax.fill(angles, vals, alpha=0.07, color=color)

    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15),
              fontsize=9, framealpha=0.85)
    ax.set_title("KPI Profile Radar — U.S. Commuter Rail Systems (FY2023)\n"
                 "Normalized 0–100 per KPI",
                 pad=20, fontsize=13, fontweight="bold",
                 color=PALETTE["navy"])

    add_footnote(fig, "Source: NTD FY2023  |  All KPIs normalized min-max to 0–100. "
                       "Cost/Trip inverted so higher = more efficient.")
    fig.savefig(os.path.join(out_dir, "fig6_radar_chart.png"))
    plt.close(fig)
    print("  ✓  fig6_radar_chart.png")


# ── Summary Stats Table ────────────────────────────────────────────────────────
def export_summary(df: pd.DataFrame, out_dir: str):
    cols = {
        "agency":             "Agency",
        "region":             "Region",
        "ridership_density":  "Ridership Density (UPT/mi)",
        "fleet_utilization":  "Fleet Utilization",
        "cost_per_trip":      "Cost per Trip ($)",
        "service_intensity":  "Service Intensity (VRM/mi)",
        "rev_hr_efficiency":  "Rev. Hr Efficiency (UPT/VRH)",
        "otp":                "On-Time Performance",
        "peak_capacity":      "Peak Capacity (seats)",
        "composite_score":    "Composite Score",
        "overall_rank":       "Overall Rank",
        "tier":               "Tier",
    }
    out = df[list(cols.keys())].rename(columns=cols)
    out["On-Time Performance"] = out["On-Time Performance"].map("{:.1%}".format)
    out["Fleet Utilization"]   = out["Fleet Utilization"].map("{:.1%}".format)
    out["Cost per Trip ($)"]   = out["Cost per Trip ($)"].map("${:.2f}".format)
    out.to_csv(os.path.join(out_dir, "summary_kpis.csv"), index=False)
    print("  ✓  summary_kpis.csv")
    return out


# ── Main ───────────────────────────────────────────────────────────────────────
def main(data_path: str = None):
    if data_path is None:
        data_path = os.path.join(DATA_DIR, "raw_data.csv")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n── Loading data ──────────────────────────────────")
    df_raw = load_data(data_path)
    print(f"   {len(df_raw)} agencies loaded from {data_path}")

    print("\n── Computing KPIs ────────────────────────────────")
    df = compute_kpis(df_raw)
    print(df[["agency", "composite_score", "overall_rank", "tier"]].to_string(index=False))

    print("\n── Generating figures ────────────────────────────")
    fig_composite_score(df, OUTPUT_DIR)
    fig_kpi_rankings(df, OUTPUT_DIR)
    fig_correlation(df, OUTPUT_DIR)
    fig_cost_vs_otp(df, OUTPUT_DIR)
    fig_ridership_density(df, OUTPUT_DIR)
    fig_radar(df, OUTPUT_DIR)

    print("\n── Exporting summary CSV ─────────────────────────")
    export_summary(df, OUTPUT_DIR)

    print(f"\n✓ All outputs saved to: {os.path.abspath(OUTPUT_DIR)}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="U.S. Commuter Rail Benchmarking Analysis")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to CSV data file (default: data/raw_data.csv)")
    args = parser.parse_args()
    main(args.data)
