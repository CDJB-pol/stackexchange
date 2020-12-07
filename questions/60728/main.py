from collections import Counter
import urllib.request, json
import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt
import matplotlib.patheffects as pe


plt.style.use("ggplot")

# Set up dictionary mapping state to number of EVs
evs_dict = {
    "AL": 9, "AK": 3, "AZ": 11, "AR": 6, "CA": 55, "CO": 9, "CT": 7, "DC": 3,
    "DE": 3, "FL": 29, "GA": 16, "HI": 4, "ID": 4, "IL": 20, "IN": 11, "IA": 6,
    "KS": 6, "KY": 8, "LA": 8, "ME": 4, "MD": 10, "MA": 11, "MI": 16, "MN": 10,
    "MS": 6, "MO": 10, "MT": 3, "NE": 5, "NV": 6, "NH": 4, "NJ": 14, "NM": 5,
    "NY": 29, "NC": 15, "ND": 3, "OH": 18, "OK": 7, "OR": 7, "PA": 20, "RI": 4,
    "SC": 9, "SD": 3, "TN": 11, "TX": 38, "UT": 6, "VT": 3, "VA": 13, "WA": 12,
    "WV": 5, "WI": 10, "WY": 3,
}


# Get house results data from NYT source
with urllib.request.urlopen(
    "https://static01.nyt.com/elections-assets/2020/data/api/2020-11-03/national-map-page/national/house.json"
) as url:
    data = json.load(url)["data"]["races"]

# Create dictionary mapping state to overall state winner
df = pd.DataFrame(
    {
        state: max(
            parties := sum(
                [
                    Counter({c["party_id"]: c["votes"] for c in race["candidates"]})
                    for race in data
                    if race["state_id"] == state
                ],
                Counter(),
            ),
            key=parties.get,
        )
        for state in set(race["state_id"] for race in data)
    }.items(),
    columns=["state", "winner"],
)

# Print out number of electoral votes for each party.
for party in set(df["winner"]):
    print(
        f"{party} electoral votes: {sum(evs_dict[state] for state in df[df['winner'] == party]['state'])}"
    )


# Shapefile not included in repo
map_df = gpd.read_file("cb_2018_us_state_500k.shp").to_crs(epsg=2163)

m = map_df["NAME"] == "Alaska"
map_df[m] = map_df[m].set_geometry(
    map_df[m].scale(0.6, 0.6, 0.6).translate(1700000, -5000000)
)

m = map_df["NAME"] == "Hawaii"
map_df[m] = map_df[m].set_geometry(map_df[m].translate(6000000, -1800000))

map_df["state"] = map_df["STUSPS"]

merged = map_df.merge(df, on="state", how="inner")

fig, ax = plt.subplots(1, dpi=800)

merged[merged["winner"] == "republican"].plot(
    facecolor="red", ax=ax, legend=False, edgecolor="0.5", linewidth=0.25
)
merged[merged["winner"] == "democrat"].plot(
    facecolor="blue", ax=ax, legend=False, edgecolor="0.5", linewidth=0.25
)

ax.axis("off")

ax.set_title("State-aggregated voting totals: 2020 House elections", fontsize=12)

merged.apply(
    lambda x: ax.text(
        x.geometry.centroid.coords[0][0],
        x.geometry.centroid.coords[0][1],
        f"{x['state']}\n{evs_dict[x['state']]}",
        ha="center",
        fontsize=4,
        color="w",
        path_effects=[pe.withStroke(linewidth=0.4, foreground="black")],
    ),
    axis=1,
)

ax.annotate(
    f"""
    Republican 'EVs': {sum(evs_dict[state] for state in df[df['winner'] == 'republican']['state'])}\n
    Democrat 'EVs': {sum(evs_dict[state] for state in df[df['winner'] == 'democrat']['state'])}
    """,
    xy=(700000, -3000000),
    xycoords="data",
)

plt.savefig("map.png", bbox_inches="tight", pad_inches=0, dpi=800)
