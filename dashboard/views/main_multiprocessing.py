import pandas as pd

# Globale vars
ds = None
shap_ds = None

def init_global_vars(_ds, _shap_ds):
    global ds, shap_ds
    ds = _ds
    shap_ds = _shap_ds

def aggregate_data(dataset, var_name, date_range, agg_method):
    da = dataset[var_name]
    if "time" in da.dims:
        start, end = map(pd.to_datetime, date_range)
        sel = da.sel(time=slice(start, end))
        try:
            return getattr(sel, agg_method)(dim="time")
        except Exception:
            return sel.sum(dim="time")
    return da

def compute_df(dataset, var_name, date_range, agg_method):
    if var_name not in dataset:
        return None
    agg_da = aggregate_data(dataset, var_name, date_range, agg_method)
    if agg_da is None:
        return None
    return agg_da.to_series().to_frame(name=var_name)

def compute_map_df(var_name, date_range, agg_method):
    return compute_df(ds, var_name, date_range, agg_method)

def compute_shap_df(var_name, date_range, agg_method):
    SHAP_VAR_MAPPING = {'P': 'sum_P', 'T': 'sum_T'}
    shap_var = (
        var_name
        if var_name in shap_ds.data_vars
        else SHAP_VAR_MAPPING.get(var_name)
    )
    df = compute_df(shap_ds, shap_var, date_range, agg_method) if shap_var else None
    if df is not None and shap_var != var_name:
        df.columns = [var_name]
    return df

def compute_runoff_df(date_range, agg_method):
    return compute_df(shap_ds, "Y", date_range, agg_method)