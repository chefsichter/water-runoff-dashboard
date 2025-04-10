import panel as pn

def create_loading_spinner():
    return pn.indicators.LoadingSpinner(visible=False, width=50, height=50,
                                          css_classes=["spinner-centered"])
