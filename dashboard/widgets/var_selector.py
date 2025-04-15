import panel as pn

def create_variable_selector(all_vars, var_metadata, initial_variable):
    var_options = {
        var_metadata.get(var, {}).get("long_name", var): var
        for var in all_vars
    }
    return pn.widgets.Select(
        name='📊 Variable',
        options=var_options,
        value=initial_variable,
        margin=(5, 0),
        sizing_mode='stretch_width'
    )