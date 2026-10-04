import json
import pandas as pd

# Load existing ranked landmarks
df = pd.read_csv("data/nc_landmarks_ranked.csv")
df["annual_views"] = df["annual_views"].fillna(0).astype(int)

# Bounding box for North Carolina
NC_BOUNDS = {"min_lat": 33.7, "max_lat": 36.6, "min_lon": -84.4, "max_lon": -75.4}

# Filter points strictly within bounds
df = df[
    (df["lat"] >= NC_BOUNDS["min_lat"])
    & (df["lat"] <= NC_BOUNDS["max_lat"])
    & (df["lon"] >= NC_BOUNDS["min_lon"])
    & (df["lon"] <= NC_BOUNDS["max_lon"])
].copy()

# Color categorization
CATEGORY_COLORS = {
    "Historic Sites": "#0D2A47",
    "Parks & Nature": "#059669",
    "Museums": "#DC2626",
    "Lighthouses": "#0284C7",
    "Archaeology": "#D97706",
    "Other": "#4B5563",
}


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


df["clean_cat"] = df["category"].apply(clean_cat)

# Normalize landmarks to 3D plane dimensions [-20 to +20 on X, -7 to +7 on Z]
landmarks_3d = []
for _, row in df.iterrows():
  norm_x = (
      (row["lon"] - NC_BOUNDS["min_lon"])
      / (NC_BOUNDS["max_lon"] - NC_BOUNDS["min_lon"])
      - 0.5
  ) * 40.0
  norm_z = (
      0.5
      - (row["lat"] - NC_BOUNDS["min_lat"])
      / (NC_BOUNDS["max_lat"] - NC_BOUNDS["min_lat"])
  ) * 15.0

  landmarks_3d.append({
      "rank": int(row["rank"]),
      "name": row["name"],
      "cat": row["clean_cat"],
      "region": row["region"],
      "views": int(row["annual_views"]),
      "x": round(norm_x, 3),
      "z": round(norm_z, 3),
      "color": CATEGORY_COLORS.get(row["clean_cat"], "#4B5563"),
  })

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>North Carolina 3D Raised Topographic Relief Model</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body, html {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background-color: #0d0f12;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    #canvas-container {{
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
    }}
    #hud {{
      position: absolute;
      top: 24px;
      left: 24px;
      color: #F1F3F5;
      z-index: 10;
      pointer-events: none;
      background: rgba(13, 15, 18, 0.75);
      backdrop-filter: blur(8px);
      padding: 16px 20px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    h1 {{
      font-size: 18px;
      margin: 0 0 4px 0;
      letter-spacing: 0.5px;
      color: #FFFFFF;
    }}
    p {{
      margin: 0;
      font-size: 11px;
      color: #9CA3AF;
    }}
    #instructions {{
      position: absolute;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      color: #9CA3AF;
      font-size: 12px;
      background: rgba(13, 15, 18, 0.75);
      padding: 8px 16px;
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      pointer-events: none;
    }}
    #tooltip {{
      position: absolute;
      display: none;
      background: rgba(17, 24, 39, 0.95);
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 12px;
      pointer-events: none;
      z-index: 20;
      border: 1px solid rgba(255, 255, 255, 0.2);
      box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }}
  </style>
  <!-- Three.js and OrbitControls -->
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
  <div id="hud">
    <h1>NORTH CAROLINA 3D RELIEF</h1>
    <p>Thermoformed Topographic Model &bull; 15&times; Elevation Exaggeration</p>
  </div>
  <div id="instructions">Left-click: Rotate 360&deg; &bull; Right-click: Pan &bull; Scroll: Zoom</div>
  <div id="tooltip"></div>
  <div id="canvas-container"></div>

  <script>
    const landmarks = {json.dumps(landmarks_3d)};

    // Setup Scene, Camera, Renderer
    const container = document.getElementById('canvas-container');
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0e1117);

    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 22, 28);

    const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.05; // Prevent camera dipping below base
    controls.minDistance = 8;
    controls.maxDistance = 60;

    // Lighting (Studio key + fill for relief definition)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.55);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfffaed, 1.2);
    sunLight.position.set(-25, 40, -15);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    scene.add(sunLight);

    const fillLight = new THREE.DirectionalLight(0x7da4d6, 0.4);
    fillLight.position.set(25, 20, 25);
    scene.add(fillLight);

    // Procedural Elevation Height Function for North Carolina
    // X: West (-20) to East (+20) | Z: North (-7.5) to South (+7.5)
    function getElevation(x, z) {{
      // Masking NC state boundary silhouette
      const normX = (x + 20) / 40; // 0 (west) to 1 (east)
      const normZ = (z + 7.5) / 15; // 0 (north) to 1 (south)

      // Rough boundary polygon test for NC shape
      if (normX < 0 || normX > 1 || normZ < 0 || normZ > 1) return 0;
      if (normX < 0.25 && normZ > 0.85) return 0; // Cut off SW notch
      if (normX > 0.65 && normZ > 0.75) return 0; // Cape Fear water notch
      if (normX > 0.75 && normZ < 0.2) return 0;  // Albemarle Sound water

      // Elevation gradient: High in the West, dropping through the Piedmont to sea level
      let height = 0;
      if (normX < 0.3) {{
        // Blue Ridge / Great Smokies
        const mountainFactor = 1 - (normX / 0.3);
        const ridges = Math.sin(x * 1.5 + z * 0.8) * Math.cos(x * 0.6 - z * 1.2);
        const peaks = Math.sin(x * 3.2) * Math.sin(z * 3.2);
        height = Math.max(0.2, (mountainFactor * 3.8) + (ridges * 0.9) + (peaks * 0.4));
      }} else if (normX < 0.65) {{
        // Rolling Piedmont
        const piedmontFactor = 1 - ((normX - 0.3) / 0.35);
        const hills = (Math.sin(x * 2.0) + Math.cos(z * 2.0)) * 0.15;
        height = Math.max(0.08, piedmontFactor * 0.9 + hills);
      }} else {{
        // Flat Coastal Plain & Outer Banks
        height = 0.04 + Math.sin(x * 5) * 0.02;
      }}
      return height;
    }}

    // 3D Terrain Mesh Construction
    const gridX = 256;
    const gridZ = 128;
    const planeGeo = new THREE.PlaneGeometry(40, 15, gridX, gridZ);
    planeGeo.rotateX(-Math.PI / 2);

    const pos = planeGeo.attributes.position;
    const colors = [];
    const colorHelper = new THREE.Color();

    for (let i = 0; i < pos.count; i++) {{
      const x = pos.getX(i);
      const z = pos.getZ(i);
      const h = getElevation(x, z);
      pos.setY(i, h);

      // Color Ramp: Deep green (coast) -> Golden Ochre (Piedmont) -> Rich Brown/Slate (Mountains)
      if (h < 0.1) {{
        colorHelper.setHex(0x3B7A57); // Coastal Plain forest/marsh
      }} else if (h < 0.8) {{
        colorHelper.setHex(0xA88B42); // Piedmont warm golden-amber
      }} else if (h < 2.0) {{
        colorHelper.setHex(0x7D5233); // Mountain foothills
      }} else {{
        colorHelper.setHex(0x4A3728); // High mountain ridge
      }}
      colors.push(colorHelper.r, colorHelper.g, colorHelper.b);
    }}

    planeGeo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    planeGeo.computeVertexNormals();

    const terrainMat = new THREE.MeshStandardMaterial({{
      vertexColors: true,
      roughness: 0.8,
      metalness: 0.1,
      flatShading: false
    }});

    const terrainMesh = new THREE.Mesh(planeGeo, terrainMat);
    terrainMesh.receiveShadow = true;
    terrainMesh.castShadow = true;
    scene.add(terrainMesh);

    // 3D Pedestal / Base Slab
    const baseGeo = new THREE.BoxGeometry(41, 0.8, 16);
    const baseMat = new THREE.MeshStandardMaterial({{ color: 0x1E242B, roughness: 0.5 }});
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.set(0, -0.42, 0);
    baseMesh.receiveShadow = true;
    scene.add(baseMesh);

    // Interactive Landmark Flag Pins
    const pinGroup = new THREE.Group();
    const pinObjects = [];

    landmarks.forEach(l => {{
      const pinH = getElevation(l.x, l.z);
      if (pinH <= 0.01) return; // Skip offshore points

      // Pin post
      const postGeo = new THREE.CylinderGeometry(0.04, 0.04, 1.2, 8);
      const postMat = new THREE.MeshStandardMaterial({{ color: 0xE5E7EB, metalness: 0.8 }});
      const post = new THREE.Mesh(postGeo, postMat);
      post.position.set(l.x, pinH + 0.6, l.z);
      post.castShadow = true;

      // Pin head sphere
      const headGeo = new THREE.SphereGeometry(0.22, 16, 16);
      const headMat = new THREE.MeshStandardMaterial({{
        color: new THREE.Color(l.color),
        roughness: 0.3,
        metalness: 0.2
      }});
      const head = new THREE.Mesh(headGeo, headMat);
      head.position.set(l.x, pinH + 1.2, l.z);
      head.userData = l;
      head.castShadow = true;

      pinGroup.add(post);
      pinGroup.add(head);
      pinObjects.push(head);
    }});
    scene.add(pinGroup);

    // Raycasting & Tooltip Hover Interaction
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const tooltip = document.getElementById('tooltip');

    window.addEventListener('mousemove', (event) => {{
      mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(pinObjects);

      if (intersects.length > 0) {{
        const target = intersects[0].object;
        const d = target.userData;
        tooltip.style.display = 'block';
        tooltip.style.left = (event.clientX + 14) + 'px';
        tooltip.style.top = (event.clientY - 14) + 'px';
        tooltip.innerHTML = `
          <strong>#${{d.rank}} ${{d.name}}</strong><br/>
          <span style="color:#9CA3AF;">${{d.cat}} &bull; ${{d.region}}</span><br/>
          Annual Views: <b>${{d.views.toLocaleString()}}</b>
        `;
        document.body.style.cursor = 'pointer';
      }} else {{
        tooltip.style.display = 'none';
        document.body.style.cursor = 'default';
      }}
    }});

    // Window Resize Handler
    window.addEventListener('resize', () => {{
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }});

    // Render Loop
    function animate() {{
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }}
    animate();
  </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
  f.write(html_content)

print(
    "3D Raised Relief Topographic Model successfully built into index.html!"
)