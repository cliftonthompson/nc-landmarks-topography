import re
import time
import urllib.parse
import pandas as pd
import requests

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

SPARQL_QUERY = """
SELECT ?item ?itemLabel ?coord ?instanceLabel ?article WHERE {
  ?item wdt:P131 ?loc.
  ?loc wdt:P131* wd:Q1454.
  
  ?item wdt:P625 ?coord.
  
  VALUES ?instance { 
    wd:Q1081138   # historic site
    wd:Q179049    # state park
    wd:Q46169     # national park
    wd:Q33506     # museum
    wd:Q4989906   # monument
    wd:Q39715     # lighthouse
    wd:Q839954    # archaeological site
    wd:Q847017    # battlefield
    wd:Q834670    # national historic landmark
  }
  ?item wdt:P31 ?instance.

  # Strictly require an English Wikipedia article
  ?article schema:about ?item ;
           schema:isPartOf <https://en.wikipedia.org/> .
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 2000
"""

POINT_REGEX = re.compile(
    r"Point\s*\(\s*([-+]?\d*\.?\d+)\s+([-+]?\d*\.?\d+)\s*\)"
)


def parse_coordinates(coord_str):
  match = POINT_REGEX.search(str(coord_str))
  if match:
    lon = float(match.group(1))
    lat = float(match.group(2))
    return lon, lat
  return None, None


def fetch_landmarks():
  headers = {
      "User-Agent": "NCLandmarksProject/1.0 (contact: user@example.com)",
      "Accept": "application/sparql-results+json",
  }
  print("Connecting to Wikidata SPARQL endpoint...")
  response = requests.get(
      WIKIDATA_ENDPOINT,
      params={"query": SPARQL_QUERY, "format": "json"},
      headers=headers,
      timeout=60,
  )
  response.raise_for_status()
  data = response.json()

  records = []
  for row in data["results"]["bindings"]:
    coord_raw = row.get("coord", {}).get("value", "")
    lon, lat = parse_coordinates(coord_raw)
    if lon is None or lat is None:
      continue

    # Strict North Carolina Bounding Box
    if not (33.5 <= lat <= 36.8 and -84.5 <= lon <= -75.0):
      continue

    name = row.get("itemLabel", {}).get("value", "Unknown Landmark")
    category = row.get("instanceLabel", {}).get("value", "Other")
    article_url = row.get("article", {}).get("value", "")
    qid = row["item"]["value"].split("/")[-1]

    records.append({
        "qid": qid,
        "name": name,
        "category": category,
        "lat": lat,
        "lon": lon,
        "article_url": article_url,
    })

  df = pd.DataFrame(records)
  df = df.drop_duplicates(subset=["qid"]).reset_index(drop=True)
  return df


def fetch_annual_views(article_url):
  """Fetch total Wikipedia page views for the full 2025 calendar year with safe percent-encoding."""
  if not isinstance(article_url, str) or not article_url.strip():
    return 0

  raw_title = article_url.split("/wiki/")[-1]
  # Standardize spaces to underscores and encode special characters (parentheses, quotes, etc.)
  clean_title = urllib.parse.quote(raw_title.replace(" ", "_"), safe="")

  url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{clean_title}/monthly/2025010100/2025123100"
  headers = {"User-Agent": "NCLandmarksProject/1.0 (contact: user@example.com)"}

  try:
    r = requests.get(url, headers=headers, timeout=6)
    if r.status_code == 200:
      items = r.json().get("items", [])
      return sum(item["views"] for item in items)
  except Exception:
    pass
  return 0


def assign_region(lon):
  if lon < -81.5:
    return "Mountain"
  elif lon < -78.5:
    return "Piedmont"
  else:
    return "Coastal Plain"


def main():
  df = fetch_landmarks()
  print(f"Retrieved {len(df)} candidate landmarks with verified Wikipedia articles.")
  print("Fetching annual Wikipedia page views...")

  views_list = []
  for idx, row in df.iterrows():
    views = fetch_annual_views(row["article_url"])
    views_list.append(views)
    if (idx + 1) % 25 == 0 or (idx + 1) == len(df):
      print(f"  Processed {idx + 1}/{len(df)}...")
    time.sleep(0.02)

  df["annual_views"] = views_list
  df["region"] = df["lon"].apply(assign_region)

  # Sort by annual views descending and compute state rank
  df = df.sort_values(by="annual_views", ascending=False).reset_index(drop=True)
  df["rank"] = df.index + 1

  output_path = "data/nc_landmarks_ranked.csv"
  df.to_csv(output_path, index=False)
  print(f"\nSuccess! Saved updated dataset to {output_path}")
  print("\nTop 35 North Carolina Landmarks (Ranks 20 to 35):")
  print(
      df[["rank", "name", "category", "region", "annual_views"]]
      .iloc[19:35]
      .to_string(index=False)
  )


if __name__ == "__main__":
  main()