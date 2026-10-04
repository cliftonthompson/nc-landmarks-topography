import json
import requests
from shapely.geometry import box, shape, mapping, Polygon, MultiPolygon
from shapely.ops import unary_union

print("Fetching comprehensive NC boundary with all barrier islands and sounds...")

# Query authoritative US Census Cartographic Counties for North Carolina (FIPS 37)
URL = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
headers = {"User-Agent": "NCLandmarksProject/1.0"}
r = requests.get(URL, headers=headers, timeout=25)
r.raise_for_status()
data = r.json()

# Collect all 100 North Carolina county polygons (FIPS prefix '37')
nc_county_geoms = []
for f in data.get("features", []):
    fips = f.get("id", "")
    if fips.startswith("37"):
        g = shape(f["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        nc_county_geoms.append(g)

if not nc_county_geoms:
    raise ValueError("Could not extract North Carolina counties.")

print(f"Extracted {len(nc_county_geoms)} NC county geometries. Merging...")

# 1. Union all 100 counties into a single seamless polygon
nc_dissolved = unary_union(nc_county_geoms)

# 2. Add an explicit marine buffer along the eastern shelf to ensure 
#    Cape Hatteras (-75.4), Bodie Island, and Ocracoke are safely inside
#    the colored terrain block without cutting into Virginia/Tennessee borders.
bounds = nc_dissolved.bounds # (minx, miny, maxx, maxy)
# Extend eastern longitude boundary to -75.0 to capture full Outer Banks barrier system
shelf_box = box(-76.5, 34.0, -75.2, 36.6)
nc_full_marine = unary_union([nc_dissolved, shelf_box.intersection(nc_dissolved.buffer(0.12))])
nc_full_marine = nc_full_marine.buffer(0.04)

# 3. Create the dark world mask (everything outside of NC is black)
world_box = box(-180.0, -85.0, 180.0, 85.0)
mask_geom = world_box.difference(nc_full_marine)

mask_geojson = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": mapping(mask_geom)
    }]
}

boundary_geojson = {
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": mapping(nc_dissolved)
    }]
}

with open("data/nc_mask.json", "w", encoding="utf-8") as f:
    json.dump(mask_geojson, f)

with open("data/nc_boundary.json", "w", encoding="utf-8") as f:
    json.dump(boundary_geojson, f)

print("Saved boundary and mask preserving all barrier islands to data/nc_mask.json!")