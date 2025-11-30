from flask import Flask, send_from_directory

import os
from dotenv import load_dotenv

from app.extension import db, migrate, login_manager, cache, socketio
from app.configs import Config, DevConf, ProdConf
from app.routes.auth_bp import auth_bp
from app.routes.main_bp import main_bp
from app.routes.posts_bp import posts_bp
from app.routes.profiles_bp import profiles_bp
from app.routes.notifications_bp import notifications_bp
from app.routes.stories_bp import stories_bp
from app.routes.messages_bp import messages_bp
from app.routes.auth_api import auth_api
from app.routes.users_api import users_api

load_dotenv()

isDev = os.getenv("FLASK_DEBUG")

def create_app():
    # App factory
    app = Flask(__name__)
    
    if isDev:
        app.config.from_object(DevConf)
    else:
        app.config.from_object(ProdConf)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)
    socketio.init_app(app)
    
    # Import SocketIO handlers
    from app import socketio_handlers
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # User loader for Flask-Login
    from app.models.users import User
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None
    
    # Ensure all tables are created on startup
    with app.app_context():
        # Import all models to register them
        from app.models.posts import Post
        from app.models.comments import Comment
        from app.models.likes import Like
        from app.models.bookmarks import Bookmark
        from app.models.follows import Follow
        from app.models.notifications import Notification
        from app.models.conversations import Conversation
        from app.models.messages import Message
        from app.models.stories import Story
        from app.models.story_views import StoryView
        from app.models.blocked_users import BlockedUser
        
        # Create all tables
        db.create_all()
    
    # Route to serve service worker
    @app.route('/service-worker.js')
    def service_worker():
        return send_from_directory(app.static_folder, 'service-worker.js', mimetype='application/javascript')
    
    # Route to serve manifest
    @app.route('/manifest.json')
    def manifest():
        return send_from_directory(app.static_folder, 'manifest.json', mimetype='application/json')
    
    # Route to serve uploaded images with security
    @app.route('/uploads/<path:folder>/<path:filename>')
    def uploaded_file(folder, filename):
        # Security: Only allow specific folders
        if folder not in ['posts', 'profiles', 'stories', 'messages']:
            from flask import abort
            abort(404)
        
        # Security: Prevent path traversal
        filename = os.path.basename(filename)
        uploads = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        
        # Ensure the path is within upload folder (prevent directory traversal)
        uploads = os.path.abspath(uploads)
        if not uploads.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
            from flask import abort
            abort(404)
        
        filepath = os.path.join(uploads, filename)
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            from flask import abort
            abort(404)
        
        return send_from_directory(uploads, filename)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(stories_bp)
    app.register_blueprint(messages_bp)
    
    # Register API Blueprints
    app.register_blueprint(auth_api)
    app.register_blueprint(users_api)
    
    # Make CSRF token available in templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        from flask import render_template
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        from flask import flash, redirect, url_for
        from flask_login import current_user
        flash('File too large. Maximum size is 16MB.', 'error')
        if current_user.is_authenticated:
            return redirect(url_for('posts.create'))
        return redirect(url_for('main.index'))
    
    return app 