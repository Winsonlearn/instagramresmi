# Instagram Clone

A full-featured Instagram clone built with Flask, featuring user authentication, posts, likes, comments, follows, bookmarks, and more.

## Features

- **User Authentication**: Secure sign up, log in, and log out with password hashing
- **Posts**: Create, view, and delete posts with image uploads (auto-resize)
- **Likes**: Like and unlike posts in real-time via AJAX
- **Comments**: Add, edit, and delete comments
- **Follow System**: Follow and unfollow other users
- **Bookmarks**: Save posts to view later
- **Profiles**: View and edit user profiles with profile pictures
- **Feed**: Personalized feed showing posts from users you follow (with pagination)
- **Explore**: Discover posts from all users (with pagination)
- **Search**: Search for users by username or name
- **Settings**: Change password and manage account settings

## Security Features

- ✅ CSRF protection (Flask-WTF)
- ✅ Path traversal protection for file uploads
- ✅ Input validation and sanitization
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection (Jinja2 auto-escaping)
- ✅ File type and size validation
- ✅ Secure filename handling
- ✅ Password hashing (Werkzeug)
- ✅ Open redirect prevention
- ✅ Error handling without exposing internals

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Set environment variable (optional):
```bash
export FLASK_DEBUG=True
```

3. Initialize database:
```bash
uv run python init_db.py
```

Or use migrations:
```bash
uv run flask db init
uv run flask db migrate -m "Initial migration"
uv run flask db upgrade
```

4. Run the application:
```bash
uv run python main.py
```

The application will be available at `http://127.0.0.1:5000`

## Project Structure

```
app/
├── __init__.py          # App factory with error handlers
├── configs.py           # Configuration classes (Dev/Prod)
├── extension.py          # Flask extensions (DB, Migrate, Login)
├── utils.py             # Utility functions (secure image upload)
├── models/              # Database models
│   ├── users.py         # User model with relationships
│   ├── posts.py         # Post model
│   ├── comments.py     # Comment model
│   ├── likes.py         # Like model
│   ├── follows.py      # Follow model
│   └── bookmarks.py     # Bookmark model
├── forms/               # WTForms
│   ├── loginForm.py
│   ├── signupForm.py
│   ├── postForm.py
│   └── commentForm.py
├── routes/              # Blueprints
│   ├── auth_bp.py       # Authentication routes
│   ├── main_bp.py       # Main routes (feed, explore, search, saved)
│   ├── posts_bp.py      # Post-related routes
│   └── profiles_bp.py   # Profile routes
└── templates/           # Jinja2 templates
    ├── base.html
    ├── index.html
    ├── feed.html
    ├── explore.html
    ├── search.html
    ├── saved.html
    ├── errors/
    │   ├── 404.html
    │   └── 500.html
    └── ...
```

## Technologies Used

- **Flask**: Web framework
- **SQLAlchemy**: ORM for database operations
- **Flask-Login**: User session management
- **Flask-Migrate**: Database migrations
- **Flask-Caching**: Server-side caching
- **WTForms**: Form handling and validation with CSRF
- **Pillow**: Image processing and optimization
- **SQLite**: Database (development)
- **Werkzeug**: Security utilities
- **JavaScript ES6+**: Client-side utilities, state management, and UI enhancements

## Performance Optimizations

- **Server-side Caching**: Flask-Caching with configurable backends (Redis/Memcached for production)
- **Client-side Caching**: In-memory cache with expiration for API responses
- **Database Optimization**: 
  - Indexes on foreign keys and frequently queried columns
  - Eager loading with `joinedload()` to prevent N+1 queries
  - Optimized query patterns
- **Image Optimization**: 
  - Lazy loading for images (Intersection Observer API)
  - Auto-resize to max 1080px width
  - JPEG compression at 85% quality
- **Pagination**: For feed and explore pages (12 items per page)
- **Bundle Optimization**: Efficient static asset delivery

## Security Best Practices

- All user inputs are validated and sanitized
- File uploads are validated (type, size, content)
- Path traversal protection
- CSRF tokens on all forms
- Secure password storage
- Error messages don't expose internal details
- SQL injection prevention via ORM

## Notes

- Images are uploaded to the `uploads/` directory
- Database is stored in `instance/site.db`
- Default profile picture is shown if user hasn't uploaded one
- Maximum file size: 16MB
- Supported image formats: PNG, JPG, JPEG, GIF, WEBP

## New Features & Enhancements

### Client-Side Utilities (`app-utils.js`)

- **State Management**: In-memory cache with expiration
- **Toast Notifications**: Beautiful, non-intrusive notifications
- **Loading States**: Visual feedback during async operations
- **Confirmation Modals**: User-friendly confirmation dialogs
- **Error Handling**: Retry mechanisms with exponential backoff
- **Lazy Loading**: Automatic lazy loading for images
- **Keyboard Shortcuts**: 
  - `Esc`: Close modals
  - `Ctrl/Cmd + K`: Search
  - `Ctrl/Cmd + N`: New post
- **Offline Detection**: Automatic offline/online detection

### Performance Improvements

- Server-side caching for explore page (60 seconds)
- Client-side API response caching (5 minutes)
- Automatic cache invalidation on data mutations
- Image lazy loading reduces initial page load time
- Optimized database queries with eager loading

### User Experience Enhancements

- Loading indicators for all async operations
- Toast notifications for user actions
- Confirmation modals for destructive actions
- Better error messages with retry suggestions
- Empty states with helpful messages
- Improved mobile responsiveness

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required
SECRET_KEY=your-secret-key-here  # Use a strong random key in production

# Optional - Flask Debug Mode
FLASK_DEBUG=True  # Set to False in production

# Optional - Database URI (defaults to SQLite)
DB_URI=sqlite:///instance/site.db

# Optional - Redis Cache (for production)
REDIS_URL=redis://localhost:6379/0
```

### Production Setup

For production deployment:

1. **Set Environment Variables**:
   ```bash
   export SECRET_KEY="your-very-secure-secret-key"
   export FLASK_DEBUG=False
   export DB_URI="postgresql://user:password@localhost/instagram_clone"
   export REDIS_URL="redis://localhost:6379/0"
   ```

2. **Update Production Config** (`app/configs.py`):
   ```python
   class ProdConf(Config):
       SECRET_KEY = os.getenv("SECRET_KEY")
       CACHE_TYPE = "RedisCache"
       CACHE_REDIS_URL = os.getenv("REDIS_URL")
       CACHE_DEFAULT_TIMEOUT = 600
   ```

3. **Use Production Database**: PostgreSQL recommended
4. **Configure File Storage**: Use S3 or similar for uploaded files
5. **Enable HTTPS**: Use reverse proxy (Nginx) with SSL
6. **Set up Logging**: Configure proper logging handlers
7. **Configure Rate Limiting**: Add Flask-Limiter for API protection
8. **Set up Monitoring**: Add error tracking (Sentry, etc.)

## Documentation

- **API Documentation**: See [API.md](API.md) for complete API endpoint documentation
- **Integration Checklist**: See [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md) for integration verification

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html
```

### Database Migrations

```bash
# Create a new migration
uv run flask db migrate -m "Description of changes"

# Apply migrations
uv run flask db upgrade

# Rollback last migration
uv run flask db downgrade
```

### Code Style

The project follows PEP 8 style guide. Use a linter:

```bash
uv run flake8 app/
uv run black app/
```

## Troubleshooting

### Cache Issues

If you're experiencing stale data:
- Clear cache: `cache.clear()` in Python shell
- Restart application
- Check cache configuration in `configs.py`

### Image Upload Issues

- Ensure `uploads/` directory exists with proper permissions
- Check file size limits (16MB default)
- Verify allowed file extensions
- Check Pillow installation

### Database Issues

- Ensure migrations are up to date: `flask db upgrade`
- Check database file permissions
- For production, verify PostgreSQL connection string

## License

This project is open source and available for educational purposes.
