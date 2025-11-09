import os, zipfile, pathlib, textwrap, datetime

root = pathlib.Path("Data_Flow_Visualizer")
dirs = ["config", "src", "docs", "build"]
for d in dirs:
    (root / d).mkdir(parents=True, exist_ok=True)

# ---------- config/data_model.yaml ----------
(root / "config/data_model.yaml").write_text(textwrap.dedent("""\
version: 1.0
author: Jefim
description: "Пример модели данных"
nodes:
  - name: Catalog_input
    layer: SharePoint
    type: Excel
    comment: "Основной справочник материалов"
  - name: Saved_progress
    layer: SharePoint
    type: Excel
    comment: "Статусы выполнения"
  - name: Work_Hours
    layer: SharePoint
    type: Excel
    comment: "Учёт рабочих часов"
  - name: Merged_Spool_Data
    layer: PowerQuery
    type: Table
    comment: "Объединённая таблица данных"
  - name: Transfer_Orders
    layer: Output
    type: Report
    comment: "Финальный отчёт"

edges:
  - from: Catalog_input
    to: Merged_Spool_Data
    transfer_type: pq
    data_type: materials
    transfer:
      - [LOT, "LOT → Merged_Spool_Data.LOT"]
      - [MFZ, "MFZ → Merged_Spool_Data.MFZ"]

  - from: Saved_progress
    to: Merged_Spool_Data
    transfer_type: pq
    data_type: progress
    transfer:
      - [Progress_Status, "Progress_Status → Merged_Spool_Data.Progress_Status"]

  - from: Work_Hours
    to: Merged_Spool_Data
    transfer_type: pq
    data_type: hours
    transfer:
      - [Worker_ID, "Worker_ID → Merged_Spool_Data.Worker_ID"]
      - [Hours, "Hours → Merged_Spool_Data.Hours"]

  - from: Merged_Spool_Data
    to: Transfer_Orders
    transfer_type: manual
    data_type: cost
    transfer:
      - [LOT, "LOT → Transfer_Orders.LOT"]
      - [Warehouse, "Warehouse → Transfer_Orders.Warehouse"]

  - from: Saved_progress
    to: Transfer_Orders
    transfer_type: planned
    data_type: documents
    transfer:
      - [Report_ID, "Report_ID → Transfer_Orders.Report_ID"]

  - from: Work_Hours
    to: Transfer_Orders
    transfer_type: pq
    data_type: workers
    transfer:
      - [Worker_ID, "Worker_ID → Transfer_Orders.Worker_ID"]
"""), encoding="utf-8")

# ---------- config/settings.yaml ----------
(root / "config/settings.yaml").write_text(textwrap.dedent("""\
visual:
  background: "#1b1b1b"
  node_font: "#0e0e0e"
  node_font_size: 14
  node_border: "#333"
  edge_width: 1.4
physics:
  enabled: true
  gravitationalConstant: -3000
  springLength: 200
  springConstant: 0.04
colors:
  data_type:
    workers: "#66c2a5"
    progress: "#fc8d62"
    hours: "#8da0cb"
    cost: "#e78ac3"
    materials: "#a6d854"
    documents: "#ffd92f"
  transfer_type:
    pq: {dashes: false, opacity: 1.0}
    manual: {dashes: true, opacity: 1.0}
    planned: {dashes: false, opacity: 0.3}
variables:
  zoom_enabled: true
  drag_nodes: true
  highlight_on_hover: true
  animation_speed: 0.3
"""), encoding="utf-8")

# ---------- src/generate_html.py ----------
(root / "src/generate_html.py").write_text(textwrap.dedent("""\
import json, yaml, pathlib

TEMPLATE = "../src/html_template.html"
YAML_FILE = "../config/data_model.yaml"
SETTINGS_FILE = "../config/settings.yaml"
OUTPUT = "../build/data_model_v1.html"

def main():
    tpl = pathlib.Path(TEMPLATE).read_text(encoding="utf-8")
    data_model = yaml.safe_load(pathlib.Path(YAML_FILE).read_text(encoding="utf-8"))
    settings = yaml.safe_load(pathlib.Path(SETTINGS_FILE).read_text(encoding="utf-8"))

    nodes = data_model.get("nodes", [])
    edges = data_model.get("edges", [])

    vis_nodes = [{"id": n["name"], "label": f"{n['name']}\\n({n.get('layer','')})", "group": n.get("layer","")}
                 for n in nodes]

    vis_edges = []
    for i, e in enumerate(edges):
        t_type = e.get("transfer_type", "pq")
        d_type = e.get("data_type", "general")
        color = settings["colors"]["data_type"].get(d_type, "#cfcfcf")
        tstyle = settings["colors"]["transfer_type"].get(t_type, {"dashes": False, "opacity": 1})
        rgba = f"rgba({int(color[1:3],16)}, {int(color[3:5],16)}, {int(color[5:7],16)}, {tstyle['opacity']})"
        vis_edges.append({
            "id": f"edge_{i}_{e['from']}_{e['to']}",
            "from": e["from"], "to": e["to"],
            "transfer": e.get("transfer", []),
            "transfer_type": t_type, "data_type": d_type,
            "color": rgba, "dashes": tstyle["dashes"],
            "arrows": {"to": {"enabled": True, "type": "arrow", "scaleFactor": 0.8}},
            "length": 250
        })

    html = tpl.replace("__VIS_NODES__", json.dumps(vis_nodes, ensure_ascii=False))
    html = html.replace("__VIS_EDGES__", json.dumps(vis_edges, ensure_ascii=False))
    pathlib.Path(OUTPUT).write_text(html, encoding="utf-8")
    print(f"✅ Сгенерировано: {pathlib.Path(OUTPUT).resolve()}")

if __name__ == "__main__":
    main()
"""), encoding="utf-8")

# ---------- src/html_template.html ----------
(root / "src/html_template.html").write_text(textwrap.dedent("""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Data Flow Visualizer</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body {margin:0;display:flex;height:100vh;background:#111;color:#eee;font-family:"Segoe UI",sans-serif;}
  #mynetwork {flex:2;background:#1b1b1b;}
  #details {flex:1;background:#141414;padding:12px;overflow-y:auto;border-left:2px solid #222;}
  #filter {padding:10px;border-bottom:1px solid #333;background:#1d1d1d;}
  table {border-collapse:collapse;width:100%;font-size:13px;margin-top:8px;}
  th,td {border:1px solid #333;padding:4px 6px;}
  th {background:#222;color:#ffdf6b;}
</style>
</head>
<body>
<div id="mynetwork"></div>
<div id="details">
  <div id="filter">
    <b>Фильтр по типу данных:</b><br>
    <label><input type="checkbox" class="dtype" value="workers" checked> workers</label><br>
    <label><input type="checkbox" class="dtype" value="progress" checked> progress</label><br>
    <label><input type="checkbox" class="dtype" value="hours" checked> hours</label><br>
    <label><input type="checkbox" class="dtype" value="cost" checked> cost</label><br>
    <label><input type="checkbox" class="dtype" value="materials" checked> materials</label><br>
    <label><input type="checkbox" class="dtype" value="documents" checked> documents</label><br>
  </div>
  <div id="info"><p>Нажмите на узел или стрелку</p></div>
</div>
<script id="VIS_NODES" type="application/json">__VIS_NODES__</script>
<script id="VIS_EDGES" type="application/json">__VIS_EDGES__</script>
<script>
const nodesRaw = JSON.parse(document.getElementById("VIS_NODES").textContent);
const edgesRaw = JSON.parse(document.getElementById("VIS_EDGES").textContent);
const nodes = new vis.DataSet(nodesRaw);
const edges = new vis.DataSet(edgesRaw);
const container = document.getElementById("mynetwork");
const network = new vis.Network(container,{nodes,edges},{
  physics:{enabled:true,barnesHut:{gravitationalConstant:-3000}},
  nodes:{shape:"box",font:{color:"#0e0e0e",size:14},borderWidth:1,margin:10,color:{background:"#1b1b1b",border:"#333"}},
  edges:{smooth:{type:"cubicBezier"},width:1.4}
});
const info=document.getElementById("info");
network.on("click",p=>{
 if(p.nodes.length>0){
  const id=p.nodes[0];
  info.innerHTML=`<h3>${id}</h3>`;
 } else if(p.edges.length>0){
  const e=edges.get(p.edges[0]);
  let html=`<h3>${e.from} → ${e.to}</h3><p><b>Тип передачи:</b> ${e.transfer_type}</p><p><b>Тип данных:</b> ${e.data_type}</p>`;
  if(e.transfer&&e.transfer.length){html+=`<table><tr><th>Поле</th><th>Описание</th></tr>`;e.transfer.forEach(t=>html+=`<tr><td>${t[0]}</td><td>${t[1]}</td></tr>`);html+=`</table>`;}
  info.innerHTML=html;
 }
});
document.querySelectorAll('.dtype').forEach(chk=>{
 chk.addEventListener('change',()=>{
  const active=Array.from(document.querySelectorAll('.dtype:checked')).map(c=>c.value);
  edgesRaw.forEach(e=>edges.update({id:e.id,hidden:!active.includes(e.data_type)}));
 });
});
</script>
</body>
</html>
"""), encoding="utf-8")

# ---------- docs/changelog.md ----------
(root / "docs/changelog.md").write_text("# 📦 Changelog\n\n## v1.0\n- Initial working version\n", encoding="utf-8")

# ---------- docs/issues.md ----------
(root / "docs/issues.md").write_text("# 🧠 Issues\n\n- [x] Initial setup\n- [x] Edge filtering by type\n- [x] Color mapping\n", encoding="utf-8")

# ---------- run_pipeline.py ----------
(root / "run_pipeline.py").write_text(textwrap.dedent("""\
import subprocess, pathlib, datetime
print("🚀 Запуск пайплайна Data Flow Visualizer...")
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
subprocess.run(["python","src/generate_html.py"], check=True)
pathlib.Path("docs/build_log.txt").write_text(f"Build at {timestamp}\\n", encoding="utf-8")
print("✅ Пайплайн завершён успешно.")
"""), encoding="utf-8")

# ---------- requirements.txt ----------
(root / "requirements.txt").write_text("pyyaml\nstreamlit\npyvis\npandas\n", encoding="utf-8")

# ---------- README.md ----------
(root / "README.md").write_text("# Data Flow Visualizer\n\nПолностью готовый пайплайн для визуализации потоков данных.\nЗапуск: pip install -r requirements.txt → python run_pipeline.py\n", encoding="utf-8")

# ---------- ZIP ----------
zip_path = pathlib.Path("Data_Flow_Visualizer.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for path in root.rglob("*"):
        z.write(path, path.relative_to(root.parent))
print(f"✅ ZIP создан: {zip_path.resolve()}")
