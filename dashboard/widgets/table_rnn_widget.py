import pandas as pd
import panel as pn

def create_rnn_sensitivity_widget(main_view, hru_clicked):
    """
    Erzeugt ein Widget mit den SHAP-Werten des RNN-Modells für ein einzelnes Catchment (hru_clicked).
    """
    try:
        # Zusammenstellen der Eingabe
        rnn_input = {}
        # Statische Merkmale
        for v in main_view.static_vars:
            rnn_input[v] = float(main_view.ds[v].sel(hru=hru_clicked).values)
        # Dynamische Sequenz der letzten 7 Tage
        date_end = pd.to_datetime(main_view.end_date)
        for i in range(6, -1, -1):
            date_i = date_end - pd.Timedelta(days=i)
            rnn_input[f'P_{i}'] = float(
                main_view.ds['P'].sel(hru=hru_clicked, time=date_i).values
            )
            rnn_input[f'T_{i}'] = float(
                main_view.ds['T'].sel(hru=hru_clicked, time=date_i).values
            )
            rnn_input[f'time_{i}'] = date_i
        df_rnn_input = pd.DataFrame([rnn_input])
        # Sensitivität berechnen
        df_rnn_sens = main_view.rnn.analyze(df_rnn_input)
        # Formatieren und lesbare Feature-Namen setzen
        rnn_sens_table = df_rnn_sens.T
        rnn_sens_table.columns = ['Beitrag [%]']
        rnn_sens_table.index.name = 'Feature'
        # Umbenennung der Features mit konkretem Datum
        new_index = []
        end_date = pd.to_datetime(main_view.end_date)
        for feat in rnn_sens_table.index:
            if feat in main_view.static_vars:
                # Statisches Merkmal: long_name
                label = main_view.var_metadata.get(feat, {}).get('long_name', feat)
            elif feat.startswith(('P_', 'T_')):
                # Dynamische Merkmale P_i, T_i
                base, idx = feat.split('_')
                i = int(idx)
                date_i = end_date - pd.Timedelta(days=i)
                longname = main_view.var_metadata.get(base, {}).get('long_name', base)
                label = f"{longname} ({date_i.date().isoformat()})"
            elif feat.startswith('year_'):
                # Jahr-Feature
                idx = int(feat.rsplit('_', 1)[1])
                date_i = end_date - pd.Timedelta(days=idx)
                label = f"Jahr ({date_i.date().isoformat()})"
            elif feat.startswith('day_of_year_'):
                # Tag-im-Jahr-Feature
                idx = int(feat.rsplit('_', 1)[1])
                date_i = end_date - pd.Timedelta(days=idx)
                label = f"Tag des Jahres ({date_i.date().isoformat()})"
            else:
                label = feat
            new_index.append(label)
        rnn_sens_table.index = new_index
        # Sortieren nach Beitrag absteigend
        rnn_sens_table.sort_values('Beitrag [%]', ascending=False, inplace=True)
        # Rundung auf 2 Dezimalstellen
        rnn_sens_table['Beitrag [%]'] = rnn_sens_table['Beitrag [%]'].round(2)
        # Tabulator mit fixer Prozent-Spalte und flexibler Feature-Spalte
        df = rnn_sens_table.reset_index()
        # Rename columns
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
        return pn.pane.Markdown(f"Fehler in RNN Sensitivitätsanalyse: {e}", width=300)