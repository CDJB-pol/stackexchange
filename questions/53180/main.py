import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from collections import Counter
import us

# Read in president result data adapted from source below
# Source: https://en.wikipedia.org/wiki/List_of_United_States_presidential_election_results_by_state
pres_df = pd.read_csv("presidential_results.csv").set_index("State")

# Read in house result data, adapted from source below
# Source: https://data.lib.vt.edu/collections/rb68xc01c
house_df = pd.read_csv("house_results.csv").set_index("State")


# Get dictionary mapping presidential election year to states voting
# differently to previous election
diff_states = {}

for y in range(1864, 2020, 4):
    pres = pres_df[str(y)].to_dict()
    house = house_df[str(y - 2)].to_dict()
    diff_states[y] = [
        k for k in pres if pres[k] != house[k] and not pd.isnull(house[k])
    ]

# Output with nicer formatting
with open("output.txt", "w") as f:
    for y in sorted(diff_states.keys(), reverse=True):
        f.write(f'{y} - {", ".join(sorted(diff_states[y]))}\n')

# Get per-state vote count
state_counts = Counter(y for x in diff_states.values() for y in x)

# Convert to df and plot
df = pd.DataFrame(state_counts.items(), columns=["State", "n"])

# Shapefile not included in repo
# Source: https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html
map_df = gpd.read_file("cb_2018_us_state_500k.shp").to_crs(epsg=2163)

# Reposition Alaska & Hawaii
m = map_df["NAME"] == "Alaska"
map_df[m] = map_df[m].set_geometry(
    map_df[m].scale(0.6, 0.6, 0.6).translate(1700000, -5000000)
)

m = map_df["NAME"] == "Hawaii"
map_df[m] = map_df[m].set_geometry(map_df[m].translate(6000000, -1800000))

# Merge & plot
map_df["State"] = map_df["NAME"]
merged = map_df.merge(df, on="State", how="inner")

fig, ax = plt.subplots(1, dpi=800)
merged.plot(
    column="n",
    cmap="Blues",
    ax=ax,
    legend=True,
    legend_kwds={"shrink": 0.7},
    edgecolor="0.5",
    linewidth=0.25,
)
ax.axis("off")
ax.set_title("Number of times a State has voted differently", fontsize=12)
merged.apply(
    lambda x: ax.annotate(
        text=f"{us.states.lookup(x['State']).abbr}\n{x['n']}",
        xy=x.geometry.centroid.coords[0],
        ha="center",
        fontsize=3,
    ),
    axis=1,
)
plt.savefig("state_map.png")
