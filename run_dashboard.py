from dashboard.app import create_app
import panel as pn

if __name__ == "__main__":
    pn.serve(create_app, title="Water Runoff Dashboard", show=True, port=1961)