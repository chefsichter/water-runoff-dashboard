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
        bootstrap.modal.append("❌ No metadata available for this variable.")
        return

    # Metadaten auslesen und Content erzeugen
    meta = var_metadata[variable]
    content = pn.pane.HTML(f"""
    <div style="display: flex; justify-content: center;">
        <div class="var-info-modal" style="
            width: 100%;
            max-width: 500px;
            font-size: 0.95rem;
            padding: 10px 10px;
            background-color: white;
        ">
            <h3 style="margin-top: 0;">🔍 Information: {variable}</h3>
            <table style="
                width: 100%;
                border-collapse: collapse;
                font-size: 0.95rem;
            ">
                <tbody>
                    <tr><th style='text-align:left; padding:10px 8px; background:#EEEEEE; width:40%;'>🏷️ Variable name</th><td style='padding:10px 8px;background:#f5f5f5;'>{meta.get("name", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#EEEEEE;'>🗺️ Description</th><td style='padding:10px 8px;background:#f5f5f5;'>{meta.get("long_name", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#EEEEEE;'>⚖️ Units</th><td style='padding:10px 8px; background:#f5f5f5;'>{meta.get("units", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#EEEEEE;'>📐 Dimensions</th><td style='padding:10px 8px;background:#f5f5f5;'>{meta.get("dims", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#EEEEEE;'>💾 Data type</th><td style='padding:10px 8px;background:#f5f5f5;'>{meta.get("dtype", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#EEEEEE;'>🗂️ Source</th><td style='padding:10px 8px;background:#f5f5f5;'>{meta.get("source", "N/A")}</td></tr>
                    <tr><th style='text-align:left; padding:10px 8px; background:#EEEEEE;'>🕓 History</th><td style='padding:10px 8px;background:#f5f5f5;'>{meta.get("history", "N/A")}</td></tr>
                </tbody>
            </table>
        </div>
    </div>
""", sizing_mode="stretch_width")





    # Neuen Modal-Inhalt anhängen
    bootstrap.modal.append(content)
    bootstrap.open_modal()


