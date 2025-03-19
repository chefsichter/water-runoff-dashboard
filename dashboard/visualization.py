import holoviews as hv
import hvplot.xarray  # Erweitert xarray um hvplot-Funktionalitäten

hv.extension('plotly')

import geopandas as gpd
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import panel as pn
import plotly.graph_objects as go


def polygon_to_3d_coords(geom, elevation: float):
    """
    Wandelt ein (Multi-)Polygon in 3D-Koordinaten um.
    Falls geom ein MultiPolygon ist, wird das größte Polygon (nach Fläche) gewählt.
    Gibt ein Dictionary mit den Listen zu 'x', 'y' und 'z' zurück.
    """
    if geom.geom_type == 'Polygon':
        poly = geom
    elif geom.geom_type == 'MultiPolygon':
        poly = max(geom.geoms, key=lambda p: p.area)
    else:
        raise ValueError("Unsupported geometry type: " + str(geom.geom_type))
    xs, ys = zip(*poly.exterior.coords)
    zs = [elevation] * len(xs)
    return {'x': list(xs), 'y': list(ys), 'z': zs}


def get_color(value, vmin, vmax, variable):
    """
    Ordnet einem numerischen Wert eine Farbe zu und liefert den Farbwert als Hex-Code.
    Für Niederschlag ('P') wird der 'Blues'-Colormap genutzt,
    für Temperatur ('T') der 'Reds'-Colormap.
    Bei anderen Variablen wird standardmäßig 'viridis' verwendet.
    """
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    if variable == 'P':
        cmap = cm.get_cmap('Blues')
    elif variable == 'T':
        cmap = cm.get_cmap('Reds')
    else:
        cmap = cm.get_cmap('viridis')
    rgba = cmap(norm(value))
    return mcolors.rgb2hex(rgba)


def create_3d_polygons(geodf, value_column: str, variable: str) -> pn.pane.Plotly:
    """
    Erzeugt ein Overlay aus allen 3D-Polygon-Objekten basierend auf dem GeoDataFrame.
    Die Farbe jedes Polygons wird anhand des Werts in value_column und des passenden Colormaps
    (abhängig von variable) berechnet.

    Das Overlay wird in eine Plotly-Figur gerendert, wobei die Kameraeinstellung so
    angepasst wird, dass aus einer Top-Down-Perspektive (x-y-Ebene als Landkarte) geschaut wird.
    Die resultierende Figur wird als Panel Plotly-Pane zurückgegeben.
    """
    vmin = geodf[value_column].min()
    vmax = geodf[value_column].max()
    polygons = []
    for idx, row in geodf.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        coords = polygon_to_3d_coords(row.geometry, row['dhm'])
        color = get_color(row[value_column], vmin, vmax, variable)
        path3d = hv.Path3D((coords['x'], coords['y'], coords['z'])).opts(
            color=color,
            line_width=2
        )
        polygons.append(path3d)
    overlay = hv.Overlay(polygons).opts(
        title="3D Catchment Map",
        width=800,
        height=800,
        show_legend=False
    )
    # Render das Overlay als Plotly-Figur
    fig = hv.render(overlay, backend='plotly')
    # Falls fig ein dict ist, in eine Plotly-Figur umwandeln:
    if isinstance(fig, dict):
        fig = go.Figure(fig)
    # Setze die Kameraeinstellung so, dass die Ansicht top-down (x-y-Ebene) ist:
    fig.update_layout(scene_camera=dict(eye=dict(x=0, y=0, z=5)))
    return pn.pane.Plotly(fig, sizing_mode='stretch_both')


def create_timeseries_plot(ds, variable: str, hru_index: int) -> hv.Element:
    """
    Erzeugt einen Zeitreihen-Plot (hvPlot) für die ausgewählte Variable und den Catchment (hru) Index.
    """
    data = ds[variable].isel(hru=hru_index)
    return data.hvplot.line(x='time', y=variable, title=f"{variable} Zeitreihe für Catchment {hru_index}")