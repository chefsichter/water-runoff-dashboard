# modal.py
import panel as pn
import textwrap

def update_modal(modal_container, var_metadata, variable):
    if variable not in var_metadata:
        pn.state.notifications.error("❌ Keine Metadaten für diese Variable vorhanden.")
        return
    meta = var_metadata[variable]
    # Erstellen des Modal-Inhalts als Markdown
    modal_content = textwrap.dedent(f"""
        ### 🔍 Information: {variable}
        | **Zusatzinformationen** |                    |
        | -------------------------- | ----------------------------- |
        | 🏷️ Variablenname          | {meta.get("name", "N/A")}      |
        | 🗺️ Bezeichnung           | {meta.get("long_name", "N/A")} |
        | ⚖️ Einheiten             | {meta.get("units", "N/A")}     |
        | 📐 Dimensionen           | {meta.get("dims", "N/A")}      |
        | 💾 Datentyp              | {meta.get("dtype", "N/A")}     |
        | 🗂️ Quelle              | {meta.get("source", "N/A")}    |
        | 🕓 Historie             | {meta.get("history", "N/A")}   |
    """)
    # Aktualisieren Sie den festen Modal-Container des Bootstrap-Templates
    modal_container.objects = [modal_content]
