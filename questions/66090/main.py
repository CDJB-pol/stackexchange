import pandas as pd
import requests
import time
import geopandas as gpd
from matplotlib import pyplot as plt
from matplotlib.pyplot import cm
import matplotlib.colors as mcol
import matplotlib.patches as mpatches
import adjustText
import numpy as np
import seaborn as sns

# Scrape mayoral results, included for completeness.
# can instead use rep_primary.csv or dem_primary.csv in repo

rep_df = pd.DataFrame({"ad": [], "ed": [], "silwa": [], "mateo": [], "writein": []})

for ad in range(23, 88):
    url = f"https://web.enrboenyc.us/CD24425AD{ad}0.html"
    df = pd.read_html(url)[2]
    df = df[2:-1]

    df["ad"] = ad
    df["ed"] = df[0].apply(lambda x: int(x.split()[1]))
    df["silwa"] = df[3]
    df["mateo"] = df[5]
    df["writein"] = df[7]
    rep_df = pd.concat([rep_df, df[["ad", "ed", "silwa", "mateo", "writein"]]])
    time.sleep(10)

dem_df = pd.DataFrame(
    {
        "ad": [],
        "ed": [],
        "foldenauer": [],
        "morales": [],
        "stringer": [],
        "mcguire": [],
        "wiley": [],
        "prince": [],
        "chang": [],
        "garcia": [],
        "adams": [],
        "wright jr": [],
        "donovan": [],
        "yang": [],
        "taylor": [],
        "writein": [],
    }
)

for ad in range(63, 88):
    url = f"https://web.enrboenyc.us/CD24306AD{ad}0.html"
    df = pd.read_html(url)[2]
    df = df[2:-1]

    df["ad"] = ad
    df["ed"] = df[0].apply(lambda x: int(x.split()[1]))
    df["foldenauer"] = df[3]
    df["morales"] = df[5]
    df["stringer"] = df[7]
    df["mcguire"] = df[9]
    df["wiley"] = df[11]
    df["prince"] = df[13]
    df["chang"] = df[15]
    df["garcia"] = df[17]
    df["adams"] = df[19]
    df["wright jr"] = df[21]
    df["donovan"] = df[23]
    df["yang"] = df[25]
    df["taylor"] = df[27]
    df["writein"] = df[29]
    dem_df = pd.concat(
        [
            dem_df,
            df[
                [
                    "ad",
                    "ed",
                    "foldenauer",
                    "morales",
                    "stringer",
                    "mcguire",
                    "wiley",
                    "prince",
                    "chang",
                    "garcia",
                    "adams",
                    "wright jr",
                    "donovan",
                    "yang",
                    "taylor",
                    "writein",
                ]
            ],
        ]
    )
    time.sleep(10)

# Identify shut-out precincts
rep_df = rep_df[rep_df["silwa"] + rep_df["mateo"] + rep_df["writein"] == 0]

# Identify precincts with at least 50 votes
dem_df = dem_df[
    dem_df["foldenauer"]
    + dem_df["morales"]
    + dem_df["stringer"]
    + dem_df["mcguire"]
    + dem_df["wiley"]
    + dem_df["prince"]
    + dem_df["chang"]
    + dem_df["garcia"]
    + dem_df["adams"]
    + dem_df["wright jr"]
    + dem_df["donovan"]
    + dem_df["yang"]
    + dem_df["taylor"]
    + dem_df["writein"]
    >= 50
]

# Inner merge to get the precincts we're interested in - shut-out_districts.csv
merged = pd.merge(
    rep_df, dem_df, how="inner", on=["ad", "ed"], suffixes=["_rep", "_dem"]
)
merged = merged[merged.columns.difference(["mateo", "silwa", "writein_rep"])]

# Plot vote-shares in Democratic primary
fig, ax = plt.subplots(1, dpi=800)
totals = merged[merged.columns.difference(["ad", "ed"])].sum()
labels = [x.capitalize() for x in totals.index]
colours = cm.rainbow(np.linspace(0, 1, len(labels)))
patches, texts = ax.pie(
    merged[merged.columns.difference(["ad", "ed"])].sum(), colors=colours
)
labels = [
    f"{x.capitalize()} - {round(100*totals[x]/sum(totals), 1)}%" for x in totals.index
]
ax.legend(patches, labels, bbox_to_anchor=(0, 1))
plt.savefig("precinct_pie.png", bbox_inches="tight", pad_inches=0, dpi=800)


merged["winner"] = merged[merged.columns.difference(["ad", "ed"])].idxmax(axis=1)
merged["ElectDist"] = merged.apply(
    lambda x: f"{x['ad']}{str(x['ed']).zfill(3)}", axis=1
).astype(int)

# Read shapefile - not included in repo
# https://www1.nyc.gov/site/planning/data-maps/open-data/districts-download-metadata.page
map_df = gpd.read_file("nyed.shp")

# Plot map of Democratic primary
merged_map = map_df.merge(merged, on="ElectDist", how="outer")
merged_map["colour"] = merged_map["winner"].apply(
    lambda x: "r"
    if x == "adams"
    else "b"
    if x == "wiley"
    else "g"
    if x == "garcia"
    else "y"
    if x == "yang"
    else "white"
)

fig, ax = plt.subplots(1, dpi=800)
merged_map.plot(
    facecolor=merged_map["colour"],
    ax=ax,
    legend=False,
    edgecolor="black",
    linewidth=0.1,
)
ax.axis("off")
ax.set_title(
    "2021 Democratic Mayoral Primary Results\n (Republican Shut-out Districts)",
    fontsize=12,
)
ax.legend(
    handles=[
        mpatches.Patch(
            color="r",
            label=f'Adams ({merged_map["colour"].value_counts().get("r",0)})',
        ),
        mpatches.Patch(
            color="b",
            label=f'Wiley ({merged_map["colour"].value_counts().get("b",0)})',
        ),
        mpatches.Patch(
            color="g",
            label=f'Garcia ({merged_map["colour"].value_counts().get("g",0)})',
        ),
        mpatches.Patch(
            color="y",
            label=f'Yang ({merged_map["colour"].value_counts().get("y",0)})',
        ),
    ],
    loc="upper left",
    prop={"size": 4.5},
)
plt.savefig("precinct_map.png", bbox_inches="tight", pad_inches=0, dpi=800)

# Read in 2020 presidential data and pivot to get party vote count
df_2020 = pd.read_csv("2020_ADED.csv")
df_2020["Party"] = df_2020["Candidate"].apply(
    lambda x: "Rep" if "Donald" in x else "Dem" if "Biden" in x else np.nan
)
df_2020 = df_2020[df_2020["Party"].isin(["Dem", "Rep"])]
df_2020["ElectDist"] = df_2020.apply(
    lambda x: f"{x['AD']}{str(x['ED']).zfill(3)}", axis=1
).astype(int)
df_2020 = df_2020.pivot_table(
    index="ElectDist", columns="Party", values="Votes", aggfunc="sum"
).reset_index()

merged = pd.merge(
    rep_df, dem_df, how="inner", on=["ad", "ed"], suffixes=["_rep", "_dem"]
)
merged["ElectDist"] = merged.apply(
    lambda x: f"{x['ad']}{str(x['ed']).zfill(3)}", axis=1
).astype(int)

merged = merged[["ad", "ed", "ElectDist"]].merge(df_2020, on="ElectDist")
merged["Dem Percent"] = (merged["Dem"] / (merged["Rep"] + merged["Dem"]) * 100).astype(
    float
)
print(merged["Dem Percent"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))

# Plot boxplot
fig, ax = plt.subplots(figsize=(8, 2))
sns.boxenplot(
    x="Dem Percent",
    data=merged,
    ax=ax,
)
plt.savefig("2020_boxplot.png", bbox_inches="tight", pad_inches=0, dpi=800)

# Plot 2020 presidential election map
merged_map = map_df.merge(merged, on="ElectDist", how="outer")

fig, ax = plt.subplots()
cm1 = mcol.LinearSegmentedColormap.from_list("RWB", ["r", "w", "b"])
merged_map.plot(
    column="Dem Percent",
    ax=ax,
    cmap=cm1,
    legend=True,
    legend_kwds={"shrink": 0.7},
    edgecolor="0.5",
    linewidth=0.25,
    missing_kwds=dict(
        color="white",
    ),
)
ax.axis("off")
ax.set_title(
    "Democrat two-party vote-share \n (Republican 2021 Mayoral Primary Shut-out Districts)",
    size=9,
)
plt.savefig("precinct_map_2020.png", bbox_inches="tight", pad_inches=0, dpi=700)
