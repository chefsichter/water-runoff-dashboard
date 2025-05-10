import pandas as pd
import panel as pn

def create_static_sensitivity_widget(main_view, hru_clicked):
    if main_view.day_stride != 1:
        return pn.pane.Markdown(
            "Statische Sensitivitätsanalyse nur für Einzel-Tages-Auswahl (day_stride=1) verfügbar.",
            width=300
        )
    try:
        static_input = {}
        for v in main_view.static_vars:
            static_input[v] = float(main_view.ds[v].sel(hru=hru_clicked).values)
        date = pd.to_datetime(main_view.start_date)
        static_input['P'] = float(main_view.ds['P'].sel(hru=hru_clicked, time=date).values)
        static_input['T'] = float(main_view.ds['T'].sel(hru=hru_clicked, time=date).values)
        static_input['time'] = date
        df_static_input = pd.DataFrame([static_input])
        df_static_sens = main_view.snn.analyze(df_static_input)
        static_sens_table = df_static_sens.T
        static_sens_table.columns = ['Beitrag [%]']
        static_sens_table.index.name = 'Feature'
        long_names = [
            main_view.var_metadata.get(f, {}).get('long_name', f)
            for f in static_sens_table.index
        ]
        static_sens_table.index = long_names
        static_sens_table.sort_values('Beitrag [%]', ascending=False, inplace=True)
        # Rundung auf 2 Dezimalstellen
        static_sens_table['Beitrag [%]'] = static_sens_table['Beitrag [%]'].round(2)
        # Tabulator: erste Spalte 'Feature', zweite fixierte Prozent-Spalte '%'
        df = static_sens_table.reset_index()
        # Umbenennen der Spalten
        df.columns = ['Feature', '%']
        return pn.widgets.Tabulator(
            df,
            show_index=False,
            layout='fit_data',
            widths={'%': 50},
            height=300,
            disabled=True
        )
    except Exception as e:
        return pn.pane.Markdown(f"Fehler in statischer Sensitivitätsanalyse: {e}", width=300)