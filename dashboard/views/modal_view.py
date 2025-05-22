import panel as pn

# Hilfsfunktion, damit der HTML-Block übersichtlicher bleibt
def _build_info_html(variable, meta):
    return f"""
    <div style="display:flex;justify-content:center">
      <div class="var-info-modal" style="width:100%;max-width:500px;
           font-size:0.95rem;padding:10px;background:white">
        <h3 style="margin-top:0">🔍 Information: {variable}</h3>
        <table style="width:100%;border-collapse:collapse;font-size:0.95rem">
          <tbody>
            <tr><th style='text-align:left;padding:10px 8px;background:#eee;width:40%'>🏷️ Variable name</th>
                <td style='padding:10px 8px;background:#f5f5f5'>{meta.get("name","N/A")}</td></tr>
            <tr><th style='text-align:left;padding:10px 8px;background:#eee'>🗺️ Description</th>
                <td style='padding:10px 8px;background:#f5f5f5'>{meta.get("long_name","N/A")}</td></tr>
            <tr><th style='text-align:left;padding:10px 8px;background:#eee'>⚖️ Units</th>
                <td style='padding:10px 8px;background:#f5f5f5'>{meta.get("units","N/A")}</td></tr>
            <tr><th style='text-align:left;padding:10px 8px;background:#eee'>📐 Dimensions</th>
                <td style='padding:10px 8px;background:#f5f5f5'>{meta.get("dims","N/A")}</td></tr>
            <tr><th style='text-align:left;padding:10px 8px;background:#eee'>💾 Data type</th>
                <td style='padding:10px 8px;background:#f5f5f5'>{meta.get("dtype","N/A")}</td></tr>
            <tr><th style='text-align:left;padding:10px 8px;background:#eee'>🗂️ Source</th>
                <td style='padding:10px 8px;background:#f5f5f5'>{meta.get("source","N/A")}</td></tr>
            <tr><th style='text-align:left;padding:10px 8px;background:#eee'>🕓 History</th>
                <td style='padding:10px 8px;background:#f5f5f5'>{meta.get("history","N/A")}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    """

def show_var_infos(bootstrap: pn.template.BootstrapTemplate,
                   var_metadata: dict,
                   variable: str):
    """
    Füllt das *bereits vorhandene* info_pane im Modal neu und öffnet es.
    """
    # Das erste Kind des Modals *ist* unser persistentes HTML-Pane
    # (wurde in app.py einmal angelegt).
    if not bootstrap.modal:
        # Fallback, falls das Pane aus Versehen gelöscht wurde
        bootstrap.modal.append(pn.pane.HTML("", sizing_mode="stretch_width"))
    info_pane = bootstrap.modal[0] # pn.pane.HTML

    # Inhalt setzen
    if variable not in var_metadata:
        info_pane.object = "<p>❌ No metadata available for this variable.</p>"
    else:
        info_pane.object = _build_info_html(variable, var_metadata[variable])

    # Modal anzeigen
    bootstrap.open_modal()
