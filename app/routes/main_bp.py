from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.extension import cache

from app.models.posts import Post
from app.models.users import User
from app.extension import db
from sqlalchemy.orm import joinedload

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """Landing page - redirect to feed if logged in, else show welcome"""
    if current_user.is_authenticated:
        return redirect(url_for('main.feed'))
    return render_template("index.html")

@main_bp.route("/feed")
@login_required
def feed():
    """Main feed showing posts from users you follow"""
    page = request.args.get('page', 1, type=int)
    
    # Get posts from users you follow + your own posts
    following_ids = [f.followed_id for f in current_user.following.all()]
    following_ids.append(current_user.id)
    
    # Get posts ordered by created_at (newest first) with pagination
    # Optimize: eager load user relationship to avoid N+1 queries
    if following_ids:
        posts_query = Post.query.filter(Post.user_id.in_(following_ids))\
                                .options(joinedload(Post.user))\
                                .order_by(Post.created_at.desc())
        posts = posts_query.paginate(page=page, per_page=12, error_out=False)
        
        # If no posts from following, show explore (all posts)
        if posts.total == 0:
            posts = Post.query.options(joinedload(Post.user))\
                              .order_by(Post.created_at.desc())\
                              .paginate(page=page, per_page=12, error_out=False)
    else:
        # User is not following anyone, show all posts
        posts = Post.query.options(joinedload(Post.user))\
                          .order_by(Post.created_at.desc())\
                          .paginate(page=page, per_page=12, error_out=False)
    
    return render_template("feed.html", posts=posts)

@main_bp.route("/explore")
@login_required
def explore():
    """Explore page showing trending posts, hashtags, and discovery"""
    from datetime import datetime, timedelta
    import re
    
    page = request.args.get('page', 1, type=int)
    hashtag = request.args.get('hashtag', '').strip().lstrip('#')
    category = request.args.get('category', 'all')  # 'all', 'trending', 'recent'
    
    # Generate cache key
    cache_key = f"explore_{page}_{hashtag}_{category}"
    
    # Check cache (60 second timeout for explore page)
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    
    posts_query = Post.query.options(joinedload(Post.user))
    
    # Filter by hashtag if provided
    if hashtag:
        posts_query = posts_query.filter(Post.caption.ilike(f'%#{hashtag}%'))
    
    # Sort by category
    if category == 'trending':
        # Sort by engagement (likes + comments) in last 24 hours
        from sqlalchemy import func
        from app.models.likes import Like
        from app.models.comments import Comment
        yesterday = datetime.utcnow() - timedelta(days=1)
        posts_query = posts_query.filter(Post.created_at >= yesterday)\
                                 .outerjoin(Like).outerjoin(Comment)\
                                 .group_by(Post.id)\
                                 .order_by(
                                     (func.count(Like.id) * 2 + func.count(Comment.id)).desc()
                                 )
    elif category == 'recent':
        posts_query = posts_query.order_by(Post.created_at.desc())
    else:  # 'all'
        # Default: mix of trending and recent
        posts_query = posts_query.order_by(Post.created_at.desc())
    
    posts = posts_query.paginate(page=page, per_page=12, error_out=False)
    
    # Get trending hashtags (hashtags with most posts in last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    # This is a simplified version - in production, you'd want a separate Hashtag table
    # For now, we'll extract from recent posts
    recent_posts = Post.query.filter(Post.created_at >= week_ago).all()
    hashtag_counts = {}
    for post in recent_posts:
        if post.caption:
            tags = re.findall(r'#(\w+)', post.caption)
            for tag in tags:
                hashtag_counts[tag.lower()] = hashtag_counts.get(tag.lower(), 0) + 1
    
    trending_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Render template
    response = render_template("explore.html", 
                             posts=posts, 
                             hashtag=hashtag,
                             category=category,
                             trending_hashtags=trending_hashtags)
    
    # Cache for 60 seconds
    cache.set(cache_key, response, timeout=60)
    
    return response

@main_bp.route("/search")
@login_required
def search():
    """Search for users and posts by hashtag"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'user')  # 'user' or 'hashtag'
    users = []
    posts = []
    
    if query and len(query) >= 2:  # Minimum 2 characters
        if search_type == 'hashtag':
            # Search posts by hashtag in caption
            hashtag = query.lstrip('#')
            posts = Post.query.filter(
                Post.caption.ilike(f'%#{hashtag}%')
            ).options(joinedload(Post.user))\
             .order_by(Post.created_at.desc())\
             .limit(50).all()
        else:
            # Search users
            users = User.query.filter(
                User.username.ilike(f'%{query}%') | 
                User.fullname.ilike(f'%{query}%')
            ).limit(20).all()
    
    return render_template("search.html", users=users, posts=posts, query=query, search_type=search_type)

@main_bp.route("/saved")
@login_required
def saved():
    """Show saved/bookmarked posts"""
    from app.models.bookmarks import Bookmark
    # Optimize: eager load post and user relationships
    bookmarks = Bookmark.query.filter_by(user_id=current_user.id)\
                              .options(joinedload(Bookmark.post).joinedload(Post.user))\
                              .order_by(Bookmark.created_at.desc())\
                              .all()
    posts = [bookmark.post for bookmark in bookmarks]
    return render_template("saved.html", posts=posts)
