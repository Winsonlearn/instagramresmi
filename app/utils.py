import os
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app

def allowed_file(filename, file_type='any'):
    """Check if file extension is allowed
    file_type: 'any', 'image', 'video'
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'image':
        return ext in current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', set())
    elif file_type == 'video':
        return ext in current_app.config.get('ALLOWED_VIDEO_EXTENSIONS', set())
    else:
        return ext in current_app.config.get('ALLOWED_EXTENSIONS', set())

def validate_image_file(file):
    """Validate image file before processing"""
    if not file or not file.filename:
        return False, "No file provided"
    
    if not allowed_file(file.filename, 'image'):
        return False, "File type not allowed. Only images are supported."
    
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 64 * 1024 * 1024)
    if size > max_size:
        return False, f"File too large. Maximum size: {max_size // (1024*1024)}MB"
    
    # Verify it's actually an image
    try:
        img = Image.open(file)
        img.verify()  # Verify it's a valid image
        file.seek(0)  # Reset file pointer
        return True, None
    except Exception as e:
        return False, "Invalid image file"

def validate_media_file(file):
    """Validate media file (image or video) before processing"""
    if not file or not file.filename:
        return False, "No file provided", None
    
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if allowed_file(file.filename, 'image'):
        media_type = 'image'
    elif allowed_file(file.filename, 'video'):
        media_type = 'video'
    else:
        return False, "File type not allowed. Only images and videos are supported.", None
    
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 64 * 1024 * 1024)
    if size > max_size:
        return False, f"File too large. Maximum size: {max_size // (1024*1024)}MB", None
    
    # Verify it's actually a valid media file
    if media_type == 'image':
        try:
            img = Image.open(file)
            img.verify()
            file.seek(0)
            return True, None, 'image'
        except Exception:
            return False, "Invalid image file", None
    else:  # video
        # For videos, we just check extension and size (could add more validation later)
        file.seek(0)
        return True, None, 'video'

def save_post_image(file, user_id, timestamp):
    """Save post image and return filename"""
    valid, error = validate_image_file(file)
    if not valid:
        return None, error
    
    try:
        # Create secure filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"post_{user_id}_{timestamp}_{secure_filename(file.filename)}"
        
        # Full path
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts')
        filepath = os.path.join(upload_folder, filename)
        
        # Open and process image
        img = Image.open(file)
        
        # Convert to RGB if necessary (for formats like PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large (max 1080px width)
        max_width = 1080
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Save image
        img.save(filepath, 'JPEG', optimize=True, quality=85)
        return filename, None
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

def save_post_media(file, user_id, timestamp, alt_text=""):
    """Save post media (image or video) and return media object"""
    valid, error, media_type = validate_media_file(file)
    if not valid:
        return None, error
    
    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"post_{user_id}_{timestamp}_{secure_filename(file.filename)}"
        
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'posts')
        filepath = os.path.join(upload_folder, filename)
        
        if media_type == 'image':
            # Process image
            img = Image.open(file)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 1080px width)
            max_width = 1080
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            img.save(filepath, 'JPEG', optimize=True, quality=85)
        else:  # video
            # For videos, save as-is (could add compression later)
            file.save(filepath)
        
        return {
            "url": filename,
            "type": media_type,
            "alt_text": alt_text
        }, None
    except Exception as e:
        return None, f"Error processing media: {str(e)}"

def save_profile_image(file, user_id):
    """Save profile image and return filename"""
    valid, error = validate_image_file(file)
    if not valid:
        return None, error
    
    try:
        # Create secure filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"profile_{user_id}_{secure_filename(file.filename)}"
        
        # Full path
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
        filepath = os.path.join(upload_folder, filename)
        
        # Open and process image
        img = Image.open(file)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to square 150x150 with cropping
        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        
        # Create square image (crop center)
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))
        img = img.resize((150, 150), Image.Resampling.LANCZOS)
        
        # Save image
        img.save(filepath, 'JPEG', optimize=True, quality=85)
        return filename, None
    except Exception as e:
        return None, f"Error processing image: {str(e)}"

def save_story_media(file, user_id, timestamp):
    """Save story media (image or video) and return filename and type"""
    valid, error, media_type = validate_media_file(file)
    if not valid:
        return None, None, error
    
    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"story_{user_id}_{timestamp}_{secure_filename(file.filename)}"
        
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'stories')
        filepath = os.path.join(upload_folder, filename)
        
        if media_type == 'image':
            # Process image for story (1080x1920 or maintain aspect ratio)
            img = Image.open(file)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize for story (max 1080px width, maintain aspect ratio)
            max_width = 1080
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            img.save(filepath, 'JPEG', optimize=True, quality=90)
        else:  # video
            # For videos, save as-is
            file.save(filepath)
        
        return filename, media_type, None
    except Exception as e:
        return None, None, f"Error processing story media: {str(e)}"

def extract_hashtags(text):
    """Extract hashtags from text"""
    if not text:
        return []
    import re
    hashtags = re.findall(r'#(\w+)', text)
    return list(set(hashtags))

def extract_mentions(text):
    """Extract user mentions from text"""
    if not text:
        return []
    import re
    mentions = re.findall(r'@(\w+)', text)
    return list(set(mentions))
