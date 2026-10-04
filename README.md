# North Carolina 3D Raised Topographic Relief & Landmarks Dashboard

An interactive, hardware-accelerated 3D raised topographic model of North Carolina featuring verified state historic sites, battlefields, state/national parks, and museums, sized and ranked by annual Wikipedia traffic.

Inspired by *Our State* magazine's chronicle of the legendary 8th grade North Carolina Project (the red 3-ring binder of maps, artifacts, and local history) and Reddit's r/dataisbeautiful.

## Live Demo
Access the live interactive WebGL relief map at:
**\https://<your-github-username>.github.io/nc-landmarks-topography/\**

## Features
- **True 3D Relief Terrain:** Hardware-accelerated elevation via MapLibre GL JS and AWS Open Data Terrarium RGB-DEM raster tiles with 3.6x vertical exaggeration.
- **Vivid Hypsometric Tints:** OpenTopo elevation coloring rendering lush coastal wetlands, warm golden Piedmont plateaus, and deep Appalachian terracotta ridges.
- **Isolated State Framing:** Surrounding states and offshore waters are masked with an inverted polygon to highlight North Carolina as a physical standalone relief model.
- **Verified Wikidata & Wikipedia Ingestion:** Landmarks queried via Wikidata SPARQL API and ranked using annual Wikipedia page view metrics from the Wikimedia REST API.
- **Dual Dashboard Panes:** Left panel tracking category and physiographic region metrics (Mountain, Piedmont, Coastal Plain); right panel featuring a Top 35 clickable leaderboard with smooth camera fly-to mechanics.

## Repository Architecture
\\\	ext
nc-landmarks-topography/
├── data/
│   ├── nc_landmarks_ranked.csv   # Ranked state landmarks with coordinates & traffic
│   ├── nc_boundary.json          # High-resolution NC perimeter vector geometry
│   └── nc_mask.json              # Inverted global mask isolating NC
├── docs/
│   └── nc_project_report.tex     # Comprehensive technical and historical LaTeX report
├── src/
│   ├── fetch_nc_landmarks.py    # SPARQL query & Wikimedia views ingestion pipeline
│   ├── fetch_nc_boundary.py     # Census county union and marine buffer generator
│   ├── build_dashboard.py       # Production MapLibre 3D relief dashboard compiler
│   └── build_3d_relief.py       # Experimental standalone Three.js procedural prototype
├── index.html                   # Deployable single-page WebGL application
├── requirements.txt             # Environment dependencies
├── .gitignore
└── README.md
\\\

## Local Execution

\\\powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Regenerate spatial boundary mask and landmark data
python src/fetch_nc_boundary.py
python src/fetch_nc_landmarks.py

# 4. Compile the dashboard
python src/build_dashboard.py

# 5. Launch locally
Start-Process .\index.html
\\\

## Data Sources & Citations
- **Elevation Base:** AWS Terrain Tiles (Terrarium RGB-DEM encoding)
- **Topographic Styling:** OpenTopoMap / SRTM
- **Administrative Boundaries:** US Census Bureau Cartographic Boundary Shapefiles (FIPS 37)
- **Entity Metadata:** Wikidata Query Service (Q1454 hierarchy)
- **Page Traffic:** Wikimedia Foundation REST API (2025 calendar baseline)
