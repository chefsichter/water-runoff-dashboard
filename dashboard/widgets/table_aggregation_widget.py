import pandas as pd
import panel as pn

def create_aggregation_widget(main_view, hru_clicked):
    """
    Erstellt die Aggregationsansicht: Tabelle mit Basiswerten für die angeklickte HRU.
    Gibt ein Tuple (widget, hru_clicked) zurück.
    """
    with main_view.show_spinner():
        var_name = main_view.variable
        if var_name is None:
            return pn.pane.Markdown("Keine Variable ausgewählt.", width=300), None
        # Vorbereitung
        time_value = main_view.date_range
        row_data = {}
        # Dynamische Gruppenvariablen (P, T) immer zuerst aggregieren
        dynamic_keys = []
        for dyn in ['P', 'T', 'Qmm_mod', 'Qmm_prevah']:
            if dyn in main_view.time_vars:
                try:
                    dyn_da = main_view._aggregate_data(dyn, time_value, main_view.day_stride)
                    row_data[dyn] = float(dyn_da.sel(hru=hru_clicked).values)
                except Exception:
                    row_data[dyn] = None
                dynamic_keys.append(dyn)
        # Aktuelle Variable (evtl. dynamisch oder statisch)
        if var_name in main_view.time_vars and var_name not in dynamic_keys:
            try:
                var_da = main_view._aggregate_data(var_name, time_value, main_view.day_stride)
                row_data[var_name] = float(var_da.sel(hru=hru_clicked).values)
            except Exception:
                row_data[var_name] = None
            dynamic_keys.append(var_name)
        elif var_name not in main_view.time_vars:
            try:
                row_data[var_name] = float(main_view.ds[var_name].sel(hru=hru_clicked).values)
            except Exception:
                row_data[var_name] = None
        # Statische Variablen
        for stat in main_view.static_vars:
            try:
                row_data[stat] = float(main_view.ds[stat].sel(hru=hru_clicked).values)
            except Exception:
                row_data[stat] = None
        # DataFrame zusammenstellen
        table_df = pd.DataFrame.from_dict(row_data, orient='index', columns=['Wert'])
        table_df.index.name = 'Variable'
        # Verwende lange Namen für Anzeige
        long_names = [
            main_view.var_metadata.get(v, {}).get('long_name', v)
            for v in table_df.index
        ]
        table_df.index = long_names
        # Reset Index für Tabulator
        df = table_df.reset_index()
        df.columns = ['Variable', 'Wert']
        # Gruppenspalte für Sortierung (P, T und ggf. aktuelles dynamisches Feature zuerst)
        dynamic_long = [main_view.var_metadata.get(k, {}).get('long_name', k) for k in dynamic_keys]
        df['Gruppe'] = df['Variable'].apply(lambda v: 'Dynamisch' if v in dynamic_long else 'Statisch')
        # Sortiere so, dass dynamische Einträge oben stehen
        df = df.sort_values('Gruppe', ascending=True)
        # Entferne Hilfsspalte
        df = df.drop(columns=['Gruppe'])
        # Widget erstellen mit Tabulator (volle Breite)
        table_widget = pn.widgets.Tabulator(
            df,
            show_index=False,
            layout='fit_data',
            widths={'Wert': 100},
            sizing_mode='stretch_width',
            disabled=True
        )
        return table_widget, hru_clicked

