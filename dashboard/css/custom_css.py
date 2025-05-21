import panel as pn

def load_custom_css():
    # Tabulator: kleinere Schrift in Tabulator-Tabellen
    pn.config.raw_css.append("""
.tabulator .tabulator-cell,
.tabulator .tabulator-col {
  font-size: 10px !important;
}
""")