import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.style.use("ggplot")

# Read 2020 results from Fox source
df_2020 = pd.read_csv(
    "https://feeds-elections.foxnews.com/archive/politics/elections/2020/3/President/county-level-results/feed_slimmer.csv"
)

# Extract useful columns
df_2020 = df_2020[[df_2020.columns[i] for i in [0, 2, 3, 5]]]
df_2020.columns = ["FIPS", "Switch", "Candidate 1", "Candidate 2"]

# Format dataframe in terms of Trump/Biden
df_2020["republican"] = df_2020.apply(
    lambda x: x["Candidate 1"] if x["Switch"] else x["Candidate 2"], axis=1
).astype(int)
df_2020["democrat"] = df_2020.apply(
    lambda x: x["Candidate 2"] if x["Switch"] else x["Candidate 1"], axis=1
).astype(int)

df_2020["FIPS"] = df_2020["FIPS"].apply(lambda x: str(x).zfill(5))

df_2020 = df_2020[["FIPS", "republican", "democrat"]]


# Read 2004 results from Harvard source
df_2004 = pd.read_csv(
    "https://dataverse.harvard.edu/api/access/datafile/3641280?format=original&gbrecs=true"
)
df_2004 = df_2004[
    (df_2004["year"] == 2004)
    & (df_2004["party"].isin(["republican", "democrat"]))
    & (~df_2004["FIPS"].isnull())
]
df_2004 = df_2004.pivot(
    index="FIPS", columns="party", values="candidatevotes"
).reset_index()
df_2004["FIPS"] = df_2004["FIPS"].astype(float).apply(lambda x: str(int(x)).zfill(5))

df_pres = df_2004.merge(df_2020, on="FIPS")
df_pres["2-party change"] = df_pres.apply(
    lambda x: (x["democrat_y"] / (x["republican_y"] + x["democrat_y"])) * 100
    - (x["democrat_x"] / (x["republican_x"] + x["democrat_x"])) * 100,
    axis=1,
)
df_pres = df_pres[["FIPS", "2-party change"]]

# Read in 2000 demographic data (Source: US Census table DP1)
df_census_2000 = pd.read_csv("census_data_2000.csv")[["GEO_ID", "POPGROUP", "DP1_C0"]][
    1:
]
df_census_2000 = df_census_2000[df_census_2000["POPGROUP"].isin([1, 2])]

df_census_2000 = df_census_2000.pivot(
    index="GEO_ID", columns="POPGROUP", values="DP1_C0"
).reset_index()
df_census_2000["Non-white percentage"] = (
    1 - df_census_2000[2] / df_census_2000[1]
) * 100


# Read in 2019 demographic data (Source: American Community Survey table DP5)
df_acs_2019 = pd.read_csv("acs_data_2019.csv")[
    ["GEO_ID", "B02001_001E", "B02001_002E"]
][1:]
df_acs_2019["Non-white percentage"] = (
    1 - df_acs_2019["B02001_002E"].astype(int) / df_acs_2019["B02001_001E"].astype(int)
) * 100

df_race = df_census_2000.merge(df_acs_2019, on="GEO_ID")
df_race["FIPS"] = df_race["GEO_ID"].apply(lambda x: str(x).split("US")[-1])
df_race["Non-white change"] = (
    df_race["Non-white percentage_y"] - df_race["Non-white percentage_x"]
).astype(float)
df_race = df_race[["FIPS", "Non-white change"]]

merged = df_pres.merge(df_race, on="FIPS")
merged.to_csv("out_data.csv", index=False)

# Plotting

fig, ax = plt.subplots()
merged.plot(x="Non-white change", y="2-party change", s=0.5, kind="scatter", ax=ax)
ax.set_xlabel("2000/19 Change in non-white population (pp)")
ax.set_ylabel("2004/20 2-party margin change (pp)")

x = merged["Non-white change"]
y = merged["2-party change"]

cc = round(merged.corr()["Non-white change"]["2-party change"], 2)

ax.annotate(
    f"Pearson's Correlation Coefficient: {cc}",
    xy=(-7, -45),
    xycoords="data",
    bbox=dict(boxstyle="round", fc="0.8"),
)

plt.savefig("graph.png", bbox_inches="tight", pad_inches=0, dpi=800)
