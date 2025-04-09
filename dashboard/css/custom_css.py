import panel as pn

def load_custom_css(script_dir):
    if script_dir:
        css_path = script_dir / "css" / "custom.css"
        if css_path.exists():
            with open(css_path, "r") as f:
                custom_css = f.read()
            pn.config.raw_css.append(custom_css)
        else:
            print(f"CSS-Datei nicht gefunden: {css_path}")
    else:
        print("Kein script_dir-Parameter übergeben. CSS konnte nicht geladen werden.")
