from app import create_app
from app.extension import socketio

if __name__ == "__main__":
    app = create_app()
    socketio.run(app, debug=True, host="127.0.0.1", port=5000, allow_unsafe_werkzeug=True)
