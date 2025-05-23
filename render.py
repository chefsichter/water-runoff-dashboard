from dashboard.app import create_app
import panel as pn

if __name__ == "__main__":
    pn.serve(
        create_app,
        title="Water Runoff Dashboard",
        address="0.0.0.0",
        port=10000,   # Render verwendet standardmäßig 10000
        allow_websocket_origin=["*"],  # Oder: ["ai4good-dashboard.onrender.com"]
        show=False
    )