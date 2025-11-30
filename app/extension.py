from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO

try:
    from flask_caching import Cache
    cache = Cache()
except ImportError:
    # Fallback cache implementation if flask-caching is not installed
    class SimpleCache:
        """Simple in-memory cache fallback"""
        def __init__(self):
            self._cache = {}
            self._timeouts = {}
        
        def init_app(self, app):
            """Initialize cache with app config (no-op for simple cache)"""
            pass
        
        def get(self, key):
            """Get value from cache"""
            if key in self._cache:
                # Check if expired
                if key in self._timeouts:
                    import time
                    if time.time() > self._timeouts[key]:
                        del self._cache[key]
                        del self._timeouts[key]
                        return None
                return self._cache[key]
            return None
        
        def set(self, key, value, timeout=None):
            """Set value in cache"""
            import time
            self._cache[key] = value
            if timeout:
                self._timeouts[key] = time.time() + timeout
            elif key in self._timeouts:
                del self._timeouts[key]
        
        def clear(self):
            """Clear all cache"""
            self._cache.clear()
            self._timeouts.clear()
    
    cache = SimpleCache()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO(cors_allowed_origins="*")
