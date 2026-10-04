import json
import pandas as pd

# Load ranked landmarks
df = pd.read_csv("data/nc_landmarks_ranked.csv")
df["annual_views"] = df["annual_views"].fillna(0).astype(int)


def clean_cat(cat):
  cat = str(cat).lower()
  if "historic" in cat or "battlefield" in cat:
    return "Historic Sites"
  if "park" in cat or "nature" in cat:
    return "Parks & Nature"
  if "museum" in cat:
    return "Museums"
  if "lighthouse" in cat:
    return "Lighthouses"
  if "archaeological" in cat:
    return "Archaeology"
  return "Other"


df["clean_category"] = df["category"].apply(clean_cat)

CATEGORY_COLORS = {
    "Historic Sites": "#0284C7",  # Sea Sky Blue
    "Parks & Nature": "#10B981",  # Vivid Emerald
    "Museums": "#EF4444",  # Crimson
    "Lighthouses": "#F59E0B",  # Gold
    "Archaeology": "#F97316",  # Tangerine
    "Other": "#94A3B8",  # Slate
}

cat_counts = df["clean_category"].value_counts().to_dict()

# GeoJSON for markers
geojson_features = []
for _, row in df.iterrows():
  geojson_features.append({
      "type": "Feature",
      "geometry": {
          "type": "Point",
          "coordinates": [float(row["lon"]), float(row["lat"])],
      },
      "properties": {
          "rank": int(row["rank"]),
          "name": row["name"],
          "cat": row["clean_category"],
          "region": row["region"],
          "views": int(row["annual_views"]),
          "color": CATEGORY_COLORS.get(row["clean_category"], "#94A3B8"),
          "url": str(row["article_url"]) if pd.notna(row["article_url"]) else "",
      },
  })

geojson_data = {"type": "FeatureCollection", "features": geojson_features}
top_35 = df.head(35).to_dict(orient="records")

with open("data/nc_mask.json", "r", encoding="utf-8") as f:
  mask_data = json.load(f)

with open("data/nc_boundary.json", "r", encoding="utf-8") as f:
  boundary_data = json.load(f)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>North Carolina 3D Raised Relief Model</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
  <link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
  
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    body, html {{
      height: 100%;
      width: 100%;
      overflow: hidden;
      background: #090B0E;
      color: #F1F3F5;
    }}
    #app-container {{
      display: flex;
      height: 100vh;
      width: 100vw;
    }}
    .sidebar {{
      width: 320px;
      height: 100%;
      background: rgba(14, 17, 23, 0.94);
      backdrop-filter: blur(16px);
      z-index: 1000;
      overflow-y: auto;
      padding: 22px;
      border-right: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      flex-direction: column;
      gap: 16px;
    }}
    #right-sidebar {{
      border-right: none;
      border-left: 1px solid rgba(255, 255, 255, 0.08);
    }}
    #map-container {{
      flex: 1;
      height: 100%;
      position: relative;
      background: #090B0E;
    }}
    #map {{
      height: 100%;
      width: 100%;
      background: #090B0E;
    }}
    h1 {{
      font-size: 19px;
      font-weight: 800;
      color: #FFFFFF;
      letter-spacing: 0.8px;
    }}
    .subtitle {{
      font-size: 11px;
      color: #94A3B8;
      margin-top: 4px;
      line-height: 1.4;
    }}
    .section-title {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.8px;
      color: #CBD5E1;
      text-transform: uppercase;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 5px;
      margin-top: 10px;
      margin-bottom: 8px;
    }}
    .stat-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .cat-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;
      margin-right: 6px;
      border: 1px solid #FFFFFF;
      box-shadow: 0 0 4px rgba(0,0,0,0.6);
    }}
    .leaderboard {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .leader-item {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 7px 10px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.03);
      font-size: 12px;
      cursor: pointer;
      border: 1px solid rgba(255, 255, 255, 0.04);
      transition: all 0.15s ease;
    }}
    .leader-item:hover {{
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.2);
    }}
    .leader-left {{
      display: flex;
      align-items: center;
      gap: 8px;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
    }}
    .leader-rank {{
      font-size: 10px;
      font-weight: 700;
      background: #334155;
      color: #fff;
      border-radius: 50%;
      min-width: 18px;
      height: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .leader-name {{
      font-weight: 600;
      color: #F8FAFC;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 165px;
    }}
    .leader-views {{
      font-size: 11px;
      color: #94A3B8;
      font-weight: 600;
    }}
    .maplibregl-popup-content {{
      background: #0F172A !important;
      color: #F8FAFC !important;
      border: 1px solid rgba(255,255,255,0.2) !important;
      border-radius: 8px !important;
      padding: 14px !important;
      box-shadow: 0 8px 30px rgba(0,0,0,0.8) !important;
    }}
  </style>
</head>
<body>
  <div id="app-container">
    
    <!-- LEFT SIDEBAR -->
    <div class="sidebar" id="left-sidebar">
      <div>
        <h1>NORTH CAROLINA 3D</h1>
        <div class="subtitle">Thermoformed Raised Topographic Model with true physical elevation hypsometric color relief.</div>
      </div>
      
      <div>
        <div class="section-title">Navigation Controls</div>
        <div class="subtitle" style="line-height: 1.6;">
          &bull; <b>Right-Click + Drag:</b> Pitch camera up/down &amp; rotate 360&deg;<br/>
          &bull; <b>Left-Click + Drag:</b> Pan across the state<br/>
          &bull; <b>Scroll Wheel:</b> Zoom directly into mountain passes
        </div>
      </div>

      <div>
        <div class="section-title">Categories</div>
        {"".join([f'''
        <div class="stat-row">
          <div><span class="cat-dot" style="background: {CATEGORY_COLORS.get(cat, '#94A3B8')};"></span>{cat}</div>
          <b>{count}</b>
        </div>
        ''' for cat, count in cat_counts.items()])}
      </div>

      <div>
        <div class="section-title">Regional Distribution</div>
        {"".join([f'''
        <div class="stat-row">
          <span>{reg}</span>
          <b>{len(df[df['region'] == reg])}</b>
        </div>
        ''' for reg in ['Mountain', 'Piedmont', 'Coastal Plain']])}
      </div>

      <div>
        <div class="section-title">Model Specifications</div>
        <div class="subtitle">
          USGS 3DEP / Terrarium RGB-DEM raster with 3.6&times; vertical exaggeration and OpenTopo hypsometric color relief.
        </div>
      </div>
    </div>

    <!-- CENTER 3D RELIEF CANVAS -->
    <div id="map-container">
      <div id="map"></div>
    </div>

    <!-- RIGHT SIDEBAR: Top 35 Leaderboard -->
    <div class="sidebar" id="right-sidebar">
      <div>
        <div class="section-title">Top 35 NC Landmarks</div>
        <div class="subtitle">Ranked by annual Wikipedia traffic</div>
      </div>
      <ul class="leaderboard">
        {"".join([f'''
        <li class="leader-item" onclick="flyToPin({item['lon']}, {item['lat']})">
          <div class="leader-left">
            <span class="leader-rank">{item['rank']}</span>
            <span class="leader-name" title="{item['name']}">{item['name']}</span>
          </div>
          <span class="leader-views">{item['annual_views']:,}</span>
        </li>
        ''' for item in top_35])}
      </ul>
    </div>
  </div>

  <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
  <script>
    const geojsonData = {json.dumps(geojson_data)};
    const maskData = {json.dumps(mask_data)};
    const boundaryData = {json.dumps(boundary_data)};

    const map = new maplibregl.Map({{
      container: 'map',
      style: {{
        version: 8,
        sources: {{
          // 1. OpenTopo Color Physical Relief (Rich greens, ambers, and mountain rock browns)
          'topo-color': {{
            type: 'raster',
            tiles: [
              'https://a.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png'
            ],
            tileSize: 256,
            attribution: 'Map style: &copy; OpenTopoMap, SRTM'
          }},
          // 2. Open Global Elevation Model (Terrarium RGB-DEM)
          'terrain-dem': {{
            type: 'raster-dem',
            tiles: [
              'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{{z}}/{{x}}/{{y}}.png'
            ],
            encoding: 'terrarium',
            tileSize: 256
          }}
        }},
        layers: [
          {{
            id: 'topo-base',
            type: 'raster',
            source: 'topo-color',
            paint: {{
              'raster-saturation': 0.35,
              'raster-contrast': 0.25
            }}
          }},
          {{
            id: 'hillshading',
            type: 'hillshade',
            source: 'terrain-dem',
            paint: {{
              'hillshade-exaggeration': 1.0,
              'hillshade-shadow-color': '#090B0E',
              'hillshade-highlight-color': '#FFFFFF'
            }}
          }}
        ]
      }},
      center: [-79.8, 35.4],
      zoom: 7.0,
      pitch: 58,     // Angled down to showcase vertical relief
      bearing: -15,  // Tilted west toward the mountain ridges
      maxPitch: 85
    }});

    map.on('load', () => {{
      // 3.6x Vertical Exaggeration for distinct raised-relief model feel
      map.setTerrain({{
        source: 'terrain-dem',
        exaggeration: 3.6
      }});

      // 1. High-Resolution Inverted Silhouette Mask (Hides everything outside NC)
      map.addSource('nc-mask', {{
        type: 'geojson',
        data: maskData
      }});
      map.addLayer({{
        id: 'mask-layer',
        type: 'fill',
        source: 'nc-mask',
        paint: {{
          'fill-color': '#090B0E',
          'fill-opacity': 1.0
        }}
      }});

      // 2. Glowing State Perimeter Ribbon
      map.addSource('nc-boundary', {{
        type: 'geojson',
        data: boundaryData
      }});
      map.addLayer({{
        id: 'boundary-glow',
        type: 'line',
        source: 'nc-boundary',
        paint: {{
          'line-color': '#38BDF8',
          'line-width': 2.2,
          'line-opacity': 0.8
        }}
      }});

      // 3. Landmark Markers
      map.addSource('nc-landmarks', {{
        type: 'geojson',
        data: geojsonData
      }});

      map.addLayer({{
        id: 'landmarks-outer',
        type: 'circle',
        source: 'nc-landmarks',
        paint: {{
          'circle-radius': [
            'interpolate', ['linear'], ['get', 'views'],
            0, 5.5,
            5000, 7.5,
            15000, 9.5,
            25000, 12
          ],
          'circle-color': '#FFFFFF',
          'circle-opacity': 1,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#000000'
        }}
      }});

      map.addLayer({{
        id: 'landmarks-inner',
        type: 'circle',
        source: 'nc-landmarks',
        paint: {{
          'circle-radius': [
            'interpolate', ['linear'], ['get', 'views'],
            0, 4,
            5000, 6,
            15000, 8,
            25000, 10.5
          ],
          'circle-color': ['get', 'color'],
          'circle-opacity': 1
        }}
      }});

      // Popup on click
      map.on('click', 'landmarks-outer', (e) => {{
        const props = e.features[0].properties;
        const coordinates = e.features[0].geometry.coordinates.slice();

        new maplibregl.Popup()
          .setLngLat(coordinates)
          .setHTML(`
            <div style="font-size: 13px;">
              <h4 style="margin: 0 0 4px 0; color: #38BDF8;">#${{props.rank}} ${{props.name}}</h4>
              <div style="font-size: 11px; color: #94A3B8; margin-bottom: 6px;">${{props.cat}} &bull; ${{props.region}}</div>
              <hr style="margin: 6px 0; border: none; border-top: 1px solid rgba(255,255,255,0.15);">
              <div><b>Annual Views:</b> ${{Number(props.views).toLocaleString()}}</div>
              ${{props.url ? `<a href="${{props.url}}" target="_blank" style="color: #38BDF8; text-decoration: none; font-size: 11px; display: inline-block; margin-top: 6px; font-weight:600;">View Wikipedia &rarr;</a>` : ''}}
            </div>
          `)
          .addTo(map);
      }});

      map.on('mouseenter', 'landmarks-outer', () => {{ map.getCanvas().style.cursor = 'pointer'; }});
      map.on('mouseleave', 'landmarks-outer', () => {{ map.getCanvas().style.cursor = ''; }});
    }});

    function flyToPin(lon, lat) {{
      map.flyTo({{
        center: [lon, lat],
        zoom: 11,
        pitch: 68,
        bearing: -20,
        essential: true,
        duration: 2200
      }});
    }}
  </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
  f.write(html_template)

print("Dashboard compiled with high-resolution state border and vibrant 3D relief!")