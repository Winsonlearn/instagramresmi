// Neon Theme Interactive Features
// Double-tap to like animation handler

document.addEventListener('DOMContentLoaded', function() {
    // Enhanced double-tap for mobile
    const postImages = document.querySelectorAll('.card-image');
    
    postImages.forEach(imageContainer => {
        let tapTimer = null;
        let tapCount = 0;
        
        imageContainer.addEventListener('touchstart', function(e) {
            e.preventDefault();
            tapCount++;
            if (tapCount === 1) {
                tapTimer = setTimeout(() => {
                    tapCount = 0;
                }, 300);
            } else if (tapCount === 2) {
                clearTimeout(tapTimer);
                tapCount = 0;
                
                const postId = this.id.replace('post-image-', '');
                showDoubleTapHeart(postId);
                
                // Auto-like if not already liked
                const likeBtn = document.getElementById(`like-btn-${postId}`);
                if (likeBtn && !likeBtn.innerHTML.includes('❤️')) {
                    toggleLike(postId);
                }
            }
        });
    });
});

function showDoubleTapHeart(postId) {
    const heart = document.getElementById(`double-tap-heart-${postId}`);
    if (!heart) return;
    
    heart.style.display = 'block';
    heart.style.position = 'absolute';
    heart.style.top = '50%';
    heart.style.left = '50%';
    heart.style.transform = 'translate(-50%, -50%)';
    heart.style.zIndex = '1000';
    heart.style.pointerEvents = 'none';
    
    // Animate heart
    heart.style.animation = 'doubleTapHeart 0.6s ease-out';
    
    setTimeout(() => {
        heart.style.display = 'none';
        heart.style.animation = '';
    }, 600);
}

// Smooth scroll to top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Add smooth transitions for links
document.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', function(e) {
        if (this.getAttribute('href') && !this.getAttribute('href').startsWith('#')) {
            // Add loading state if needed
            if (this.classList.contains('btn')) {
                this.style.opacity = '0.7';
            }
        }
    });
});

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 16px 24px;
        background: rgba(26, 26, 26, 0.95);
        backdrop-filter: blur(20px);
        border: 2px solid;
        border-radius: 12px;
        color: var(--neon-blue);
        box-shadow: var(--glow-blue);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        max-width: 300px;
    `;
    
    if (type === 'success') {
        toast.style.borderColor = 'var(--neon-green)';
        toast.style.color = 'var(--neon-green)';
        toast.style.boxShadow = 'var(--glow-green)';
    } else if (type === 'error') {
        toast.style.borderColor = 'var(--neon-pink)';
        toast.style.color = 'var(--neon-pink)';
        toast.style.boxShadow = 'var(--glow-pink)';
    }
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Add CSS animations for toasts
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Press 'L' to like/unlike current post (if focused)
    if (e.key === 'l' || e.key === 'L') {
        const focusedElement = document.activeElement;
        if (focusedElement.closest('.card')) {
            const postCard = focusedElement.closest('.card');
            const likeBtn = postCard.querySelector('[id^="like-btn-"]');
            if (likeBtn) {
                const postId = likeBtn.id.replace('like-btn-', '');
                toggleLike(parseInt(postId));
            }
        }
    }
    
    // Press '/' to focus search
    if (e.key === '/' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        const searchLink = document.querySelector('a[href*="search"]');
        if (searchLink) {
            searchLink.click();
        }
    }
});

// Haptic feedback simulation (for mobile)
function hapticFeedback(type = 'light') {
    if ('vibrate' in navigator) {
        if (type === 'light') {
            navigator.vibrate(10);
        } else if (type === 'medium') {
            navigator.vibrate(20);
        } else if (type === 'heavy') {
            navigator.vibrate([10, 50, 10]);
        }
    }
}

// Add haptic feedback to interactive elements
document.querySelectorAll('.btn, .card-actions a, .card-actions button').forEach(element => {
    element.addEventListener('click', function() {
        hapticFeedback('light');
    });
});

