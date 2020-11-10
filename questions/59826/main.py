import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

df = pd.read_csv(
    "https://feeds-elections.foxnews.com/archive/politics/elections/2020/3/President/county-level-results/feed_slimmer.csv"
)

# Extract useful columns
df["Total Votes"] = df[[df.columns[i] for i in range(3, len(df.columns), 2)]].sum(
    axis=1
)
df = df[[df.columns[i] for i in [0, 2, 3, 5, len(df.columns) - 1]]]
df.columns = ["FIPS", "Switch", "Candidate 1", "Candidate 2", "Total Votes"]

# Format dataframe in terms of Trump/Biden
df["Trump"] = df.apply(
    lambda x: x["Candidate 1"] if x["Switch"] else x["Candidate 2"], axis=1
)
df["Biden"] = df.apply(
    lambda x: x["Candidate 2"] if x["Switch"] else x["Candidate 1"], axis=1
)

# Add zeroes to FIPS
df["FIPS"] = df["FIPS"].apply(lambda x: str(x).zfill(5))

df = df[["FIPS", "Trump", "Biden", "Total Votes"]]

df.to_csv("county_results.csv")

print(f"Biden won counties: {len(df[df['Biden']>df['Trump']])} out of {len(df)}")
print(f"Trump votes: {int(sum(df['Trump']))}")
print(f"Biden votes: {int(sum(df['Biden']))}")

# Load in 2019 County shapefile - not included in repo.
# Source: https://www2.census.gov/geo/tiger/TIGER2019/COUNTY/
map_df = gpd.read_file("tl_2019_us_county.shp").to_crs(epsg=2163)

# Reposition Hawaii
m = map_df["STATE_NAME"] == "Hawaii"
map_df[m] = map_df[m].set_geometry(map_df[m].translate(5500000, -1800000))

# Merge dataframes
merged = map_df.merge(df, on="FIPS", how="inner")

# Set up facecolour column
merged["colour"] = df.apply(lambda x: "b" if x["Biden"] > x["Trump"] else "r", axis=1)

# Plot map
fig, ax = plt.subplots(1, dpi=800)
merged.plot(
    facecolor=merged["colour"], ax=ax, legend=False, edgecolor="black", linewidth=0.1
)
ax.axis("off")
ax.set_title("County-level victor - 2020 Presidential Election", fontsize=12)
plt.savefig("county_map.png")
