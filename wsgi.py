from app import create_app
from app.extension import socketio

app = create_app()

if __name__ != "__main__":
    # untuk production (Gunicorn)
    pass

