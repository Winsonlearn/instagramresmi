import os
from dotenv import load_dotenv

load_dotenv()

# Get the base directory of the project
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config():
    SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32).hex()
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024  # 64MB max file size (for videos)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi'}  # Added video formats
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi'}
    
    # Ensure upload directories exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'posts'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'stories'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'messages'), exist_ok=True)
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Cache configuration
    CACHE_TYPE = "SimpleCache"  # Use SimpleCache for development (in-memory)
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default timeout
    # For production, set CACHE_TYPE to "RedisCache" or "MemcachedCache"
    # CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class DevConf(Config):
    SECRET_KEY = "SECRET"
    # Use absolute path for database
    instance_path = os.path.join(basedir, 'instance')
    os.makedirs(instance_path, exist_ok=True)  # Ensure instance directory exists
    db_file = os.path.join(instance_path, 'site.db')
    # Use 4 slashes for absolute path in SQLite URI
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_file}"

class ProdConf(Config):
    SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32).hex()
    # Use DB_URI from env, or fallback to SQLite
    if not os.getenv("DB_URI"):
        instance_path = os.path.join(basedir, 'instance')
        os.makedirs(instance_path, exist_ok=True)
        db_file = os.path.join(instance_path, 'site.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_file}"
    # Production cache configuration - uncomment and configure based on your setup
    # CACHE_TYPE = "RedisCache"
    # CACHE_REDIS_URL = os.getenv("REDIS_URL")
    # CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes for production