import panel as pn
import textwrap

def show_var_infos(bootstrap: pn.template.BootstrapTemplate, var_metadata, variable):
    """
    Aktualisiert den Modal-Dialog mit den Metadaten zur aktuell ausgewählten Variable.
    Vorherigen Inhalt entfernen und neuen Inhalt anhängen.
    """
    # Alten Inhalt des Modal-Bereichs entfernen
    bootstrap.modal.clear()

    # Falls keine Metadaten zur übergebenen Variable vorliegen, Fehlermeldung anzeigen
    if variable not in var_metadata:
        bootstrap.modal.append("❌ Keine Metadaten für diese Variable vorhanden.")
        return

    # Metadaten auslesen und Content erzeugen
    meta = var_metadata[variable]
    content = textwrap.dedent(f"""
        ### 🔍 Information: {variable}
        | **Zusatzinformationen** |                    |
        | ------------------------- | ------------------ |
        | 🏷️ Variablenname          | {meta.get("name", "N/A")}      |
        | 🗺️ Bezeichnung           | {meta.get("long_name", "N/A")} |
        | ⚖️ Einheiten             | {meta.get("units", "N/A")}     |
        | 📐 Dimensionen           | {meta.get("dims", "N/A")}      |
        | 💾 Datentyp              | {meta.get("dtype", "N/A")}     |
        | 🗂️ Quelle               | {meta.get("source", "N/A")}    |
        | 🕓 Historie             | {meta.get("history", "N/A")}   |
    """)

    # Neuen Modal-Inhalt anhängen
    bootstrap.modal.append(content)
    bootstrap.open_modal()


