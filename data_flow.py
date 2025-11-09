import streamlit as st
from pyvis.network import Network

# --- ДАННЫЕ ---
nodes = [
    ("Catalog_input", "Excel", "SharePoint"),
    ("Saved_progress", "Excel", "SharePoint"),
    ("TO_RECEIVE_MOBILE", "Excel", "SharePoint"),
    ("Merged_Spool_Data", "Table", "PowerQuery"),
    ("Valve_Join", "Table", "PowerQuery"),
    ("Transfer Orders", "Report", "Output"),
    ("Grouped by Location", "Report", "Output"),
]

edges = [
    ("Catalog_input", "Merged_Spool_Data"),
    ("Catalog_input", "Valve_Join"),
    ("Catalog_input", "Grouped by Location"),
    ("Grouped by Location", "Catalog_input"),
    ("Saved_progress", "Merged_Spool_Data"),
    ("TO_RECEIVE_MOBILE", "Merged_Spool_Data"),
    ("Merged_Spool_Data", "Transfer Orders"),
    ("Valve_Join", "Grouped by Location"),
]

# --- ВИЗУАЛИЗАЦИЯ ---
net = Network(height="700px", width="100%", bgcolor="#202225", font_color="white", directed=True)

# Цвета по слоям
layer_colors = {
    "SharePoint": "#FFD580",
    "PowerQuery": "#85C1E9",
    "Output": "#58D68D"
}

for name, t, layer in nodes:
    net.add_node(name, label=f"{name}\n({t})", color=layer_colors[layer], title=f"Layer: {layer}")

for source, target in edges:
    net.add_edge(source, target, color="#AAAAAA")

# --- Streamlit интерфейс ---
st.set_page_config(page_title="Data Model Visualization", layout="wide")
st.title("📊 SharePoint → Power Query → Output Model")
st.caption("Интерактивная схема данных. Наведи курсор на узел, чтобы увидеть уровень. Двигай элементы для анализа.")

net.save_graph("data_model.html")
with open("data_model.html", "r", encoding="utf-8") as f:
    html_content = f.read()
st.components.v1.html(html_content, height=800, scrolling=True)
