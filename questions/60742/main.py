from urllib.request import Request, urlopen
import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib.colors as mcol

plt.style.use("seaborn")

req = Request(
    "https://vote.nyc/sites/default/files/pdf/election_results/2020/20201103General%20Election/00000100000Citywide%20President%20Vice%20President%20Citywide%20EDLevel.csv"
)
req.add_header(
    "User-Agent",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
)
content = urlopen(req)
df_2020 = pd.read_csv(
    content,
    usecols=[11, 12, 20, 21],
    names=["AD", "ED", "Party", "Votes"],
    thousands=",",
)
df_2020 = df_2020[
    df_2020["Party"].isin(
        [
            "Donald J. Trump / Michael R. Pence (Republican)",
            "Joseph R. Biden / Kamala D. Harris (Democratic)",
            "Donald J. Trump / Michael R. Pence (Conservative)",
            "Joseph R. Biden / Kamala D. Harris (Working Families)",
        ]
    )
]

df_2020["Precinct"] = df_2020.apply(
    lambda x: f"{str(x['ED']).zfill(3)}/{x['AD']}", axis=1
)

df_2020 = df_2020.pivot(index="Precinct", columns="Party", values="Votes").reset_index()
df_2020["Trump"] = df_2020["Donald J. Trump / Michael R. Pence (Republican)"].astype(
    int
) + df_2020["Donald J. Trump / Michael R. Pence (Conservative)"].astype(int)
df_2020["Biden"] = df_2020["Joseph R. Biden / Kamala D. Harris (Democratic)"].astype(
    int
) + df_2020["Joseph R. Biden / Kamala D. Harris (Working Families)"].astype(int)
df_2020 = df_2020[["Precinct", "Trump", "Biden"]]
df_2020["Trump Pct"] = df_2020["Trump"] / (df_2020["Biden"] + df_2020["Trump"]) * 100
df_2020 = df_2020[~df_2020["Trump Pct"].isna()]

req = Request(
    "https://vote.nyc/sites/default/files/pdf/election_results/2016/20161108General%20Election/00000100000Citywide%20President%20Vice%20President%20Citywide%20EDLevel.csv"
)
req.add_header(
    "User-Agent",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
)
content = urlopen(req)
df_2016 = pd.read_csv(
    content, usecols=[0, 1, 9, 10], names=["AD", "ED", "Party", "Votes"], thousands=","
)
df_2016 = df_2016[
    df_2016["Party"].isin(
        [
            "Donald J. Trump / Michael R. Pence (Republican)",
            "Hillary Clinton / Tim Kaine (Women's Equality)",
            "Donald J. Trump / Michael R. Pence (Conservative)",
            "Hillary Clinton / Tim Kaine (Working Families)",
            "Hillary Clinton / Tim Kaine (Democratic)",
        ]
    )
]

df_2016["Precinct"] = df_2016.apply(
    lambda x: f"{str(x['ED']).zfill(3)}/{x['AD']}", axis=1
)

df_2016 = df_2016.pivot(index="Precinct", columns="Party", values="Votes").reset_index()
df_2016["Trump"] = df_2016[
    "Donald J. Trump / Michael R. Pence (Republican)"
].str.replace(",", "").fillna(0).astype(int) + df_2016[
    "Donald J. Trump / Michael R. Pence (Conservative)"
].str.replace(
    ",", ""
).fillna(
    0
).astype(
    int
)
df_2016["Clinton"] = (
    df_2016["Hillary Clinton / Tim Kaine (Women's Equality)"]
    .str.replace(",", "")
    .fillna(0)
    .astype(int)
    + df_2016["Hillary Clinton / Tim Kaine (Working Families)"]
    .str.replace(",", "")
    .fillna(0)
    .astype(int)
    + df_2016["Hillary Clinton / Tim Kaine (Democratic)"]
    .str.replace(",", "")
    .fillna(0)
    .astype(int)
)
df_2016 = df_2016[["Precinct", "Trump", "Clinton"]]
df_2016["Trump Pct"] = df_2016["Trump"] / (df_2016["Clinton"] + df_2016["Trump"]) * 100
df_2016 = df_2016[~df_2016["Trump Pct"].isna()]

# Output stats
print(df_2016["Trump Pct"].describe(percentiles=[0.025, 0.25, 0.5, 0.75, 0.975]))
print(df_2020["Trump Pct"].describe(percentiles=[0.025, 0.25, 0.5, 0.75, 0.975]))

df_merged = df_2020.merge(
    df_2016, on="Precinct", how="outer", suffixes=("_2020", "_2016")
)[["Precinct", "Trump Pct_2020", "Trump Pct_2016"]]

# Plot graph
fig, ax = plt.subplots()
sns.boxenplot(
    y="year",
    x="value",
    data=df_merged.melt(id_vars=["Precinct"], var_name="year"),
    ax=ax,
)
ax.set_xlabel("Trump Vote Share (%)")
ax.set_yticklabels(["2020", "2016"])
ax.set_ylabel("Year")
ax.set_title("Distribution of Trump vote share in NYC precincts")
ax.set_xticks(list(range(0, 105, 5)))

plt.savefig("graph.png", bbox_inches="tight", pad_inches=0, dpi=400)

# Remove ED 61-64, no data for 2016
df_merged = df_merged[~df_merged["Precinct"].str.contains("/64|/63|/62|/61")]

# Calculate change in Trump vote %
df_merged["Shift"] = df_merged["Trump Pct_2020"] - df_merged["Trump Pct_2016"]

# Shapefile from https://geodata.lib.berkeley.edu/catalog/nyu-2451-34548
map_df = gpd.read_file("nyu_2451_34548.shp").to_crs(epsg=2163)
map_df["Precinct"] = map_df["ElectDist"].apply(lambda x: f"{str(x)[2:]}/{str(x)[:2]}")
map_merged = map_df.merge(df_merged, on="Precinct", how="inner")

# Plot map
fig, ax = plt.subplots()
cm1 = mcol.LinearSegmentedColormap.from_list("RWB", ["b", "w", "r"])
map_merged.plot(
    column="Shift",
    ax=ax,
    cmap=cm1,
    legend=True,
    legend_kwds={"shrink": 0.7},
    edgecolor="0.5",
    linewidth=0.25,
    missing_kwds=dict(
        color="lightgrey",
    ),
)
ax.axis("off")
ax.set_title("Increase in Trump two-party vote share: 2016-2020")

plt.savefig("map.png", bbox_inches="tight", pad_inches=0, dpi=500)
