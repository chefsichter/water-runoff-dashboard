from dashboard.app import create_app
import panel as pn

if __name__ == "__main__":
    app = create_app()
    pn.serve(app, title="Water Runoff Dashboard", show=True, port=1961)