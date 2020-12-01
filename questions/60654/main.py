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


# Read 2016 results from Harvard source
df_2016 = pd.read_csv(
    "https://dataverse.harvard.edu/api/access/datafile/3641280?format=original&gbrecs=true"
)
df_2016 = df_2016[
    (df_2016["year"] == 2016)
    & (df_2016["party"].isin(["republican", "democrat"]))
    & (~df_2016["FIPS"].isnull())
]
df_2016 = df_2016.pivot(
    index="FIPS", columns="party", values="candidatevotes"
).reset_index()
df_2016["FIPS"] = df_2016["FIPS"].astype(float).apply(lambda x: str(int(x)).zfill(5))

df_pres = df_2016.merge(df_2020, on="FIPS")
df_pres["2-party change"] = df_pres.apply(
    lambda x: (x["democrat_y"] / (x["republican_y"] + x["democrat_y"])) * 100
    - (x["democrat_x"] / (x["republican_x"] + x["democrat_x"])) * 100,
    axis=1,
)
df_pres = df_pres[["FIPS", "2-party change"]]

# Read in county data from ACS source (reformatted from original)
df_degree = pd.read_csv("degree_data.csv")
df_degree["FIPS"] = df_degree["id"].apply(lambda x: str(x).split("US")[-1])
df_degree["Degree_percent"] = df_degree["Degree_percent"] * 100
df_degree = df_degree[["FIPS", "Degree_percent"]]

final_df = df_degree.merge(df_pres, on="FIPS")
final_df.to_csv("out_data.csv", index=False)

fig, ax = plt.subplots()
final_df.plot(x="Degree_percent", y="2-party change", s=0.5, kind="scatter", ax=ax)
ax.set_xlabel("Population with Bachelor's degree or higher (%)")
ax.set_ylabel("2016/20 2-party margin change (pp)")

while True:
    try:
        z = np.polyfit(final_df["Degree_percent"], final_df["2-party change"], 1)
        break
    except:
        continue
p = np.poly1d(z)

ax.plot(
    np.unique(final_df["Degree_percent"]),
    p(np.unique(final_df["Degree_percent"])),
    "r--",
    alpha=0.5,
)

cc = round(final_df.corr()["Degree_percent"]["2-party change"], 2)
beta = round(z[0], 1)

ax.annotate(
    f"Pearson's Correlation Coefficient: {cc}\n Trend line gradient: {beta}",
    xy=(20, -27.5),
    xycoords="data",
    bbox=dict(boxstyle="round", fc="0.8"),
)

plt.savefig("graph.png", bbox_inches="tight", pad_inches=0, dpi=800)
