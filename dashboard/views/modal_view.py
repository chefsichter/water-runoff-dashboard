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
    content = pn.pane.HTML(f"""
    <div style="display: flex; justify-content: center;">
        <div class="var-info-modal" style="
            width: 100%;
            max-width: 500px;
            font-size: 0.95rem;
            border: 1px solid #ddd;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            padding: 30px 25px;
            background-color: white;
        ">
            <h3 style="margin-top: 0;">🔍 Information: {variable}</h3>
            <table style="
                width: 100%;
                border-collapse: collapse;
                font-size: 0.95rem;
            ">
                <tbody>
                    <tr><th style='text-align:left; padding:10px 8px; background:#f5f5f5; width:40%;'>🏷️ Variablenname</th><td style='padding:10px 8px;'>{meta.get("name", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#f5f5f5;'>🗺️ Bezeichnung</th><td style='padding:10px 8px;'>{meta.get("long_name", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#f5f5f5;'>⚖️ Einheiten</th><td style='padding:10px 8px;'>{meta.get("units", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#f5f5f5;'>📐 Dimensionen</th><td style='padding:10px 8px;'>{meta.get("dims", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#f5f5f5;'>💾 Datentyp</th><td style='padding:10px 8px;'>{meta.get("dtype", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#f5f5f5;'>🗂️ Quelle</th><td style='padding:10px 8px;'>{meta.get("source", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#f5f5f5;'>🕓 Historie</th><td style='padding:10px 8px;'>{meta.get("history", "N/A")}</td></tr>
                </tbody>
            </table>
        </div>
    </div>
""", sizing_mode="stretch_width")





    # Neuen Modal-Inhalt anhängen
    bootstrap.modal.append(content)
    bootstrap.open_modal()


