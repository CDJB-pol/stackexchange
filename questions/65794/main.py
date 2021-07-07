import pandas as pd
import geopandas as gpd
from matplotlib import pyplot as plt
from matplotlib import patheffects as pe
import adjustText

state_codes = {'53': 'WA', '10': 'DE', '11': 'DC', '55': 'WI', '54': 'WV',
               '15': 'HI', '12': 'FL', '56': 'WY', '72': 'PR', '34': 'NJ',
               '35': 'NM', '48': 'TX', '22': 'LA', '37': 'NC', '38': 'ND',
               '31': 'NE', '47': 'TN', '36': 'NY', '42': 'PA', '02': 'AK',
               '32': 'NV', '33': 'NH', '51': 'VA', '08': 'CO', '06': 'CA',
               '01': 'AL', '05': 'AR', '50': 'VT', '17': 'IL', '13': 'GA',
               '18': 'IN', '19': 'IA', '25': 'MA', '04': 'AZ', '16': 'ID',
               '09': 'CT', '23': 'ME', '24': 'MD', '40': 'OK', '39': 'OH',
               '49': 'UT', '29': 'MO', '27': 'MN', '26': 'MI', '44': 'RI',
               '20': 'KS', '30': 'MT', '28': 'MS', '45': 'SC', '21': 'KY',
               '41': 'OR', '46': 'SD'}

# Data not included in repo - see https://cces.gov.harvard.edu
df = pd.read_csv("CCES20_Common_OUTPUT.csv")

df = (
    df.groupby(["inputstate", "pid3"])["commonweight"]
    .sum()
    .unstack(fill_value=0)
    .drop(5, axis=1)
    .reset_index()
)

df.columns = ["State", "Democrat", "Republican", "Independent", "Other"]
df["Total"] = df["Democrat"] + df["Republican"] + df["Independent"] + df["Other"]
df["Percent lead"] = df.apply(
    lambda x: abs((x["Democrat"] - x["Republican"]) / x["Total"]) * 100, axis=1
)
df["Colour"] = df.apply(
    lambda x: "b" if x["Democrat"] > x["Republican"] else "r", axis=1
)
df["Normalised lead"] = df["Percent lead"].apply(lambda x: x / df["Percent lead"].max())

# Shapefile not included in repo - see 
# https://www.census.gov/geographies/mapping-files/2018/geo/carto-boundary-file.html
map_df = gpd.read_file("cb_2018_us_state_500k.shp").to_crs(epsg=2163)

m = map_df["NAME"] == "Alaska"
map_df[m] = map_df[m].set_geometry(
    map_df[m].scale(0.6, 0.6, 0.6).translate(1700000, -5000000)
)

m = map_df["NAME"] == "Hawaii"
map_df[m] = map_df[m].set_geometry(map_df[m].translate(6000000, -1800000))

map_df["State"] = map_df["STATEFP"].astype(int)

merged = map_df.merge(df, on="State", how="inner")

fig, ax = plt.subplots(1, dpi=800)

merged.boundary.plot(ax=ax, edgecolor="0.5", linewidth=0.25)

merged.plot(
    facecolor=merged["Colour"],
    ax=ax,
    legend=False,
    edgecolor="none",
    alpha=0.2 + 0.8 * merged["Normalised lead"],
)

ax.axis("off")

ax.set_title("Percentage point lead in party self-identification - 2020", fontsize=9)

merged.apply(
    lambda x: ax.text(
        x.geometry.centroid.coords[0][0],
        x.geometry.centroid.coords[0][1],
        f"{round(x['Percent lead'])}pp",
        ha="center",
        fontsize=4,
        color="w",
        path_effects=[pe.withStroke(linewidth=0.4, foreground="black")],
    ),
    axis=1,
)

adjustText.adjust_text(ax.texts)

plt.savefig("map.png", bbox_inches="tight", pad_inches=0, dpi=800)

df["State"] = df["State"].apply(lambda x: state_codes[str(x).zfill(2)])
df["Democrat lead"] = df["Percent lead"] * ((df["Republican"] < df["Democrat"]) * 2 - 1)
df.sort_values("Democrat lead", ascending=False)[
    ["State", "Democrat", "Republican", "Independent", "Other", "Democrat lead"]
].to_csv("out.csv", index=False)
