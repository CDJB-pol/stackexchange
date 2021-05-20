import pandas as pd
import urllib.request, json

pres_df = pd.read_csv('pres-by-cd.csv')

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

merged = pres_df.merge(house_df, on="CD")
merged.to_csv('out.csv', index=False)

biden_voters_in_rep_cds = sum(merged[merged['house_winner'] == 'republican']['Biden'])
trump_voters_in_dem_cds = sum(merged[merged['house_winner'] == 'democrat']['Trump'])




