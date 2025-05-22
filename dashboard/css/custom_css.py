import panel as pn

def load_custom_css():
    # Tabulator: kleinere Schrift in Tabulator-Tabellen
    pn.config.raw_css.append("""
.tabulator .tabulator-cell,
.tabulator .tabulator-col {
  font-size: 10px !important;
}
""")
    # Modal-Styles überschreiben – GANZ am Anfang
    pn.config.raw_css.append("""
    .modal-dialog {
        max-width: 520px !important;  /* enger als vorher (600px) */
        width: 90%;  /* mobile-friendly */
        margin: 1.75rem auto;  /* optional: etwas Abstand nach oben/unten */
    }
    .modal-content {
        padding: 0px;  /* Padding hier auf 0, weil du es im .var-info-modal selbst machst */
    }
    """)