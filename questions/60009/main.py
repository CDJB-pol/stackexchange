import numpy as np
import math
import pandas as pd
import requests
import us
from adjustText import adjust_text
from matplotlib import pyplot as plt

# Calculate studentized residuals - for detecting outliers
def internally_studentized_residual(X, Y):
    """
    https://stackoverflow.com/a/57155553/12366110
    """
    X = np.array(X, dtype=float)
    Y = np.array(Y, dtype=float)
    mean_X = np.mean(X)
    mean_Y = np.mean(Y)
    n = len(X)
    diff_mean_sqr = np.dot((X - mean_X), (X - mean_X))
    beta1 = np.dot((X - mean_X), (Y - mean_Y)) / diff_mean_sqr
    beta0 = mean_Y - beta1 * mean_X
    y_hat = beta0 + beta1 * X
    residuals = Y - y_hat
    h_ii = (X - mean_X) ** 2 / diff_mean_sqr + (1 / n)
    Var_e = math.sqrt(sum((Y - y_hat) ** 2) / (n - 2))
    SE_regression = Var_e * ((1 - h_ii) ** 0.5)
    studentized_residuals = residuals / SE_regression
    return studentized_residuals


# ----- Scraping -----

# Get 2020 per-state presidential vote counts from Dave Leip's Election Atlas

url = "https://uselectionatlas.org/RESULTS/data.php?year=2020&datatype=national&def=1&f=1&off=0&elect=0"

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

r = requests.get(url, headers=header)

dfs_2020 = pd.read_html(r.text)

# Truncate data to the 50 states (and D.C.)
df_2020 = dfs_2020[2][1:52][["State", "Biden.1", "Trump.1"]]
df_2020.columns = ["State", "2020 D", "2020 R"]

# Repeat for 2016

url = "https://uselectionatlas.org/RESULTS/data.php?year=2016&datatype=national&def=1&f=1&off=0&elect=0"

r = requests.get(url, headers=header)

dfs_2016 = pd.read_html(r.text)

df_2016 = dfs_2016[2][1:52][["State", "Clinton.1", "Trump.1"]]
df_2016.columns = ["State", "2016 D", "2016 R"]

# Get urbanization indexes from 538 article

url = "https://fivethirtyeight.com/features/how-urban-or-rural-is-your-state-and-what-does-that-mean-for-the-2020-election/"

r = requests.get(url, headers=header)

dfs_538 = pd.read_html(r.text)

urbanization_dfs = [
    dfs_538[0][["State", "Urbanization Index"]],
    dfs_538[0][["State.1", "Urbanization Index.1"]],
]

for df in urbanization_dfs:
    df.columns = ["State", "Urbanization Index"]

urbanization_df = pd.concat(urbanization_dfs)

# Merge dataframes, we lose D.C. as 538 doesn't provide an urbanization index
df = pd.merge(df_2016, df_2020, on="State")
df = pd.merge(urbanization_df, df, on="State", how="inner")

# Calculate victory margins
df["Margin of Victory 2020"] = (
    (df["2020 D"] - df["2020 R"]) / (df["2020 D"] + df["2020 R"]) * 100
)
df["Margin of Victory 2016"] = (
    (df["2016 D"] - df["2016 R"]) / (df["2016 D"] + df["2016 R"]) * 100
)

df["Winner Color 2016"] = df["Margin of Victory 2016"].apply(
    lambda x: "r" if x < 0 else "b"
)
df["Winner Color 2020"] = df["Margin of Victory 2020"].apply(
    lambda x: "r" if x < 0 else "b"
)

df["State Abbrv"] = df["State"].apply(lambda x: us.states.lookup(x).abbr)

# Calculate residuals
df["Residuals 2016"] = internally_studentized_residual(
    df["Urbanization Index"], df["Margin of Victory 2016"]
)
df["Residuals 2020"] = internally_studentized_residual(
    df["Urbanization Index"], df["Margin of Victory 2020"]
)

df.to_csv("data.csv")

# ----- Plotting -----

plt.style.use("ggplot")

# 2016

fig, ax = plt.subplots(dpi=300, figsize=(8, 4))

df.plot(
    kind="scatter",
    x="Urbanization Index",
    y="Margin of Victory 2016",
    ax=ax,
    c="Winner Color 2016",
)

texts = []

for i, txt in enumerate(df["State Abbrv"]):
    texts.append(
        plt.text(df["Urbanization Index"][i], df["Margin of Victory 2016"][i], txt)
    )

ax.set_ylim([-60, 50])
ax.set_xlim([8, 12.6])

ax.set_xticks(np.arange(8, 13, 0.5))
ax.set_yticks([-60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50])
ax.set_yticklabels(
    [
        "R+60",
        "R+50",
        "R+40",
        "R+30",
        "R+20",
        "R+10",
        "Even",
        "D+10",
        "D+20",
        "D+30",
        "D+40",
        "D+50",
    ]
)
ax.set_title("Relationship between Urbanization & 2016 two-party presidential vote")

adjust_text(
    texts,
    only_move={"points": "y", "texts": "y"},
    arrowprops=dict(arrowstyle="->", color="black", lw=0.5),
    ax=ax,
)

while True:
    try:
        z = np.polyfit(df["Urbanization Index"], df["Margin of Victory 2016"], 1)
        break
    except:
        continue
p = np.poly1d(z)
ax.plot(np.arange(8.2, 12.6, 0.01), p(np.arange(8.2, 12.6, 0.01)), "b--", alpha=0.5)

cc = round(df.corr()["Urbanization Index"]["Margin of Victory 2016"], 2)
beta = round(z[0], 1)

ax.annotate(
    f"Pearson's Correlation Coefficient: {cc}\n Trend line gradient: {beta}",
    xy=(10.5, -45),
    xycoords="data",
    bbox=dict(boxstyle="round", fc="0.8"),
)

plt.savefig("2016.png")

# 2020

fig, ax = plt.subplots(dpi=300, figsize=(8, 4))

df.plot(
    kind="scatter",
    x="Urbanization Index",
    y="Margin of Victory 2020",
    ax=ax,
    c="Winner Color 2020",
)

texts = []

for i, txt in enumerate(df["State Abbrv"]):
    texts.append(
        plt.text(df["Urbanization Index"][i], df["Margin of Victory 2020"][i], txt)
    )

ax.set_ylim([-60, 50])
ax.set_xlim([8, 12.6])

ax.set_xticks(np.arange(8, 13, 0.5))
ax.set_yticks([-60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50])
ax.set_yticklabels(
    [
        "R+60",
        "R+50",
        "R+40",
        "R+30",
        "R+20",
        "R+10",
        "Even",
        "D+10",
        "D+20",
        "D+30",
        "D+40",
        "D+50",
    ]
)
ax.set_title("Relationship between Urbanization & 2020 two-party presidential vote")

adjust_text(
    texts,
    only_move={"points": "y", "texts": "y"},
    arrowprops=dict(arrowstyle="->", color="black", lw=0.5),
    ax=ax,
)

while True:
    try:
        z = np.polyfit(df["Urbanization Index"], df["Margin of Victory 2020"], 1)
        break
    except:
        continue

p = np.poly1d(z)
ax.plot(np.arange(8.2, 12.6, 0.01), p(np.arange(8.2, 12.6, 0.01)), "b--", alpha=0.5)

cc = round(df.corr()["Urbanization Index"]["Margin of Victory 2020"], 2)
beta = round(z[0], 1)

ax.annotate(
    f"Pearson's Correlation Coefficient: {cc}\n Trend line gradient: {beta}",
    xy=(10.5, -45),
    xycoords="data",
    bbox=dict(boxstyle="round", fc="0.8"),
)

plt.savefig("2020.png")
