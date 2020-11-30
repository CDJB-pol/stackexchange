import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import geopandas as gpd
import urllib.request, json

# Read presidential results from Daily Kos source
pres_df = pd.read_html(
    "https://docs.google.com/spreadsheets/d/1XbUXnI9OyfAuhP5P3vWtMuGc5UJlrhXbzZo3AwMuHtk/htmlview#gid=0"
)[0]

# Reformat dataframe
pres_df.columns = pres_df.iloc[1]
pres_df = pres_df[3:].iloc[:, [1, 4, 5]]

# Make CD column consistent
pres_df["CD"] = pres_df["CD"].apply(lambda x: x.replace("-AL", "-01"))

# Create winner column
pres_df["pres_winner"] = pres_df.apply(
    lambda x: "democrat"
    if x["Biden"] > x["Trump"]
    else "republican"
    if x["Biden"] < x["Trump"]
    else "uncalled",
    axis=1,
)

# Read house results from NYT source
with urllib.request.urlopen(
    "https://static01.nyt.com/elections-assets/2020/data/api/2020-11-03/national-map-page/national/house.json"
) as url:
    data = json.load(url)["data"]["races"]

# Set up house results dataframe
house_df = pd.DataFrame(
    {
        "CD": [f"{race['state_id']}-{str(race['seat']).zfill(2)}" for race in data],
        "house_winner": [race["leader_party_id"] for race in data],
    }
)

# Merge the two dataframes and create map colour column accordingly
merged = pres_df.merge(house_df, on="CD")

merged["colour"] = merged.apply(
    lambda x: "b"
    if x["pres_winner"] == x["house_winner"] == "democrat"
    else "r"
    if x["pres_winner"] == x["house_winner"] == "republican"
    else "c"
    if x["pres_winner"] == "republican" and x["house_winner"] == "democrat"
    else "m"
    if x["pres_winner"] == "democrat" and x["house_winner"] == "republican"
    else "gray",
    axis=1,
)

merged.to_csv("results.csv", index=False)

# Shapefile not included in repo - source: dkel.ec/map
map_df = gpd.read_file("HexCDv21/HexCDv21.shp")
map_df = map_df[map_df.geometry.notnull()]

map_df["CDFIPS"] = map_df["GEOID"].apply(lambda x: "01" if x[2:] == "00" else x[2:])
map_df["CD"] = map_df.apply(lambda x: f"{x['STATEAB']}-{x['CDFIPS']}", axis=1)

map_merged = map_df.merge(merged, on="CD")

# Map plotting
fig, ax = plt.subplots(1)
map_merged.plot(facecolor=map_merged["colour"], edgecolor="0.6", ax=ax, linewidth=0.5)

ax.axis("off")
ax.set_title("2020 Presidential Winner & House Party by CD")
ax.legend(
    handles=[
        mpatches.Patch(
            color="r",
            label=f'Trump-Republican ({merged["colour"].value_counts().get("r",0)})',
        ),
        mpatches.Patch(
            color="b",
            label=f'Biden-Democrat ({merged["colour"].value_counts().get("b",0)})',
        ),
        mpatches.Patch(
            color="c",
            label=f'Trump-Democrat ({merged["colour"].value_counts().get("c",0)})',
        ),
        mpatches.Patch(
            color="m",
            label=f'Biden-Republican ({merged["colour"].value_counts().get("m",0)})',
        ),
        mpatches.Patch(
            color="gray",
            label=f'Not Yet Available ({merged["colour"].value_counts().get("gray",0)})',
        ),
    ],
    loc="upper left",
    prop={"size": 5.5},
)

map_merged.apply(
    lambda x: ax.annotate(
        text=x["CDLABEL"], xy=x.geometry.centroid.coords[0], ha="center", fontsize=2
    ),
    axis=1,
)

plt.savefig("map.png", bbox_inches="tight", pad_inches=0, dpi=600)
