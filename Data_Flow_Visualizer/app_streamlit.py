import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
import yaml
import pathlib
import subprocess

# --------- Настройки страницы ---------
st.set_page_config(page_title="Data Flow Visualizer Editor", layout="wide")

CONFIG_PATH = pathlib.Path("config/data_model.yaml")
GENERATOR = pathlib.Path("src/generate_html.py")
BUILD_HTML = pathlib.Path("build/data_model_v1.html")

# --------- Загрузка YAML ---------
@st.cache_data
def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

# --------- Функция генерации HTML ---------
def generate_html():
    subprocess.run(["python", str(GENERATOR)], check=True)

# --------- UI ---------
st.title("🧩 Data Flow Visualizer — YAML Editor")

col1, col2 = st.columns([2, 1])

# ---------- Левая колонка: граф ----------
with col1:
    st.subheader("🔗 Визуализация модели данных")
    try:
        generate_html()  # генерируем актуальную версию HTML
        html_code = BUILD_HTML.read_text(encoding="utf-8")
        st.components.v1.html(html_code, height=850, scrolling=True)
    except Exception as e:
        st.error(f"Не удалось загрузить визуализацию: {e}")

# ---------- Правая колонка: редактирование ----------
with col2:
    st.subheader("✏️ Редактирование YAML")

    data_model = load_yaml(CONFIG_PATH)
    node_names = [n["name"] for n in data_model.get("nodes", [])]

    # выбор узла
    selected_node_name = st.selectbox("Выберите узел для редактирования", node_names)
    node = next((n for n in data_model["nodes"] if n["name"] == selected_node_name), None)

    if node:
        st.markdown(f"#### 🧱 {node['name']}")
        col_a, col_b = st.columns(2)
        node["layer"] = col_a.text_input("Слой", value=node.get("layer", ""))
        node["type"] = col_b.text_input("Тип", value=node.get("type", ""))
        node["comment"] = st.text_area("Комментарий", value=node.get("comment", ""), height=80)

        # таблица колонок
        st.markdown("##### 📋 Колонки таблицы")

        columns_df = pd.DataFrame(node.get("columns", []))
        if columns_df.empty:
            columns_df = pd.DataFrame(columns=["name", "type", "description", "comment"])

        gb = GridOptionsBuilder.from_dataframe(columns_df)
        gb.configure_default_column(editable=True, wrapText=True, autoHeight=True, resizable=True)
        gb.configure_grid_options(enableRangeSelection=True, rowSelection="single")
        gb.configure_side_bar()
        grid_options = gb.build()

        grid_response = AgGrid(
            columns_df,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            height=400,
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=True,
            theme="streamlit",
            key=f"grid_{selected_node_name}"
        )

        updated_data = grid_response["data"].to_dict(orient="records")

        # ---- Одна кнопка: сохранить + перегенерировать + обновить ----
        st.markdown("---")
        if st.button("💾 Сохранить и перегенерировать HTML"):
            try:
                node["columns"] = updated_data

                # --- принудительно сбрасываем YAML на диск ---
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    yaml.dump(data_model, f, allow_unicode=True, sort_keys=False)
                    f.flush()
                    import os

                    os.fsync(f.fileno())  # гарантируем запись на диск

                # --- теперь запускаем генератор ---
                generate_html()

                st.success("✅ YAML сохранён, HTML перегенерирован.")
                st.rerun()

            except Exception as e:
                st.error(f"Ошибка при сохранении или генерации: {e}")

