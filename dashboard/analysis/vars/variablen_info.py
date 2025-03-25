import xarray as xr
import pandas as pd
from pathlib import Path
from tabulate import tabulate
script_dir = Path(__file__).resolve().parent

# NetCDF-Datei laden (Ersetze 'datei.nc' mit deinem Dateipfad)
nc_data = xr.open_dataset(script_dir.parent.parent.parent / "data" / "CHRUN" / "chrun.nc")

# Metadaten auslesen
data = []
for var_name, var in nc_data.variables.items():
    metadata = [
        var_name,  # Variablenname
        var.attrs.get("long_name", "N/A"),  # Langname
        var.attrs.get("units", "N/A"),  # Einheiten
        ", ".join(var.dims),  # Dimensionen
        str(var.dtype),  # Datentyp
        var.attrs.get("source", "N/A"),  # Quelle
        # var.attrs.get("references", "N/A"),  # Referenzen
        var.attrs.get("history", "N/A"),  # Historie
    ]
    data.append(metadata)

# "Referenzen" nachfolgend weggelassen
headers = ["Variablenname", "Langer Name", "Einheiten", "Dimensionen", "Datentyp", "Quelle", "Historie"]

# Tabelle mit tabulate ausgeben
print(tabulate(data, headers=headers, tablefmt="grid"))  # Alternativ: "pretty", "fancy_grid"