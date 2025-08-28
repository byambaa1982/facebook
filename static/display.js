/**
 * Facebook Posts & Comments Dashboard JavaScript
 * =============================================
 * 
 * Handles dynamic loading and display of posts and comments from the database
 */

class PostsDisplay {
    constructor() {
        this.posts = [];
        this.filteredPosts = [];
        this.currentSearch = '';
        this.filters = {
            withComments: false,  // Show all posts by default
            facebookPosts: false  // Show all posts by default
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadData();
    }
    
    bindEvents() {
        // Search functionality
        const searchInput = document.getElementById('search-input');
        const searchBtn = document.getElementById('search-btn');
        const clearSearch = document.getElementById('clear-search');
        
        searchBtn.addEventListener('click', () => this.performSearch());
        clearSearch.addEventListener('click', () => this.clearSearch());
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        searchInput.addEventListener('input', () => {
            if (searchInput.value.trim() === '') {
                this.clearSearch();
            }
        });
        
        // Filter functionality
        document.getElementById('filter-with-comments').addEventListener('change', (e) => {
            this.filters.withComments = e.target.checked;
            this.applyFilters();
        });
        
        document.getElementById('filter-facebook-posts').addEventListener('change', (e) => {
            this.filters.facebookPosts = e.target.checked;
            this.applyFilters();
        });
    }
    
    async loadData() {
        try {
            this.showLoading(true);
            
            // Load posts and database stats in parallel
            const [postsResponse, statsResponse] = await Promise.all([
                fetch('/api/posts-with-comments'),
                fetch('/api/database-stats')
            ]);
            
            if (!postsResponse.ok || !statsResponse.ok) {
                throw new Error('Failed to load data');
            }
            
            const postsData = await postsResponse.json();
            const statsData = await statsResponse.json();
            
            if (postsData.success) {
                this.posts = postsData.posts;
                this.updateHeaderStats(postsData);
                this.applyFilters();
            } else {
                throw new Error(postsData.error || 'Failed to load posts');
            }
            
            if (statsData.success) {
                this.updateDatabaseStats(statsData.stats);
                document.getElementById('db-stats').style.display = 'block';
            }
            
        } catch (error) {
            this.showError('Failed to load posts and comments: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    updateHeaderStats(data) {
        const totalComments = data.posts.reduce((sum, post) => {
            return sum + (post.comments ? post.comments.total_comments : 0);
        }, 0);
        
        const postsWithComments = data.posts.filter(post => 
            post.comments && post.comments.total_comments > 0
        ).length;
        
        document.getElementById('total-posts').textContent = data.total_posts;
        document.getElementById('total-comments').textContent = totalComments;
        document.getElementById('posts-with-comments').textContent = postsWithComments;
    }
    
    updateDatabaseStats(stats) {
        document.getElementById('db-total-keys').textContent = stats.total_keys || 0;
        document.getElementById('db-content-keys').textContent = stats.content_keys || 0;
        document.getElementById('db-comment-keys').textContent = stats.comment_keys || 0;
        document.getElementById('db-facebook-posts').textContent = stats.posts_with_facebook_id || 0;
    }
    
    performSearch() {
        const searchInput = document.getElementById('search-input');
        const query = searchInput.value.trim();
        
        if (!query) {
            this.clearSearch();
            return;
        }
        
        this.currentSearch = query.toLowerCase();
        this.applyFilters();
        
        // Show clear button
        document.getElementById('clear-search').style.display = 'inline-block';
    }
    
    clearSearch() {
        document.getElementById('search-input').value = '';
        document.getElementById('clear-search').style.display = 'none';
        this.currentSearch = '';
        this.applyFilters();
    }
    
    applyFilters() {
        let filtered = [...this.posts];
        
        // Apply search filter
        if (this.currentSearch) {
            filtered = filtered.filter(post => {
                const title = (post.title || '').toLowerCase();
                const content = (post.content || '').toLowerCase();
                return title.includes(this.currentSearch) || content.includes(this.currentSearch);
            });
        }
        
        // Apply checkbox filters only if they are checked
        if (this.filters.withComments) {
            filtered = filtered.filter(post => 
                post.comments && post.comments.total_comments > 0
            );
        }
        
        if (this.filters.facebookPosts) {
            filtered = filtered.filter(post => 
                post.facebook_post_id && post.posted_to_facebook
            );
        }
        
        this.filteredPosts = filtered;
        this.renderPosts();
    }
    
    renderPosts() {
        const container = document.getElementById('posts-container');
        const noResults = document.getElementById('no-results');
        
        if (this.filteredPosts.length === 0) {
            container.style.display = 'none';
            noResults.style.display = 'block';
            return;
        }
        
        container.style.display = 'block';
        noResults.style.display = 'none';
        
        container.innerHTML = '';
        
        this.filteredPosts.forEach(post => {
            const postElement = this.createPostElement(post);
            container.appendChild(postElement);
        });
    }
    
    createPostElement(post) {
        const template = document.getElementById('post-template');
        const postElement = template.content.cloneNode(true);
        
        // Fill in post data
        const titleElement = postElement.querySelector('.post-title');
        const textElement = postElement.querySelector('.post-text');
        const idElement = postElement.querySelector('.post-id');
        const facebookIdElement = postElement.querySelector('.facebook-post-id');
        const createdElement = postElement.querySelector('.post-created');
        
        titleElement.textContent = post.title || 'Untitled Post';
        textElement.textContent = post.content || 'No content available';
        idElement.textContent = post.id || 'Unknown';
        facebookIdElement.textContent = post.facebook_post_id || 'Not posted to Facebook';
        createdElement.textContent = this.formatDate(post.created_at);
        
        // Show badges
        if (post.posted_to_facebook) {
            postElement.querySelector('.facebook-badge').style.display = 'flex';
        }
        
        if (post.comments && post.comments.total_comments > 0) {
            const commentsBadge = postElement.querySelector('.comments-badge');
            commentsBadge.style.display = 'flex';
            commentsBadge.querySelector('.comment-count').textContent = post.comments.total_comments;
        }
        
        // Add event listeners
        const toggleBtn = postElement.querySelector('.toggle-btn');
        const postDetails = postElement.querySelector('.post-details');
        
        toggleBtn.addEventListener('click', () => {
            postDetails.classList.toggle('visible');
            toggleBtn.classList.toggle('active');
        });
        
        // Handle comments
        this.setupCommentsSection(postElement, post);
        
        // Add animation
        const postCard = postElement.querySelector('.post-card');
        postCard.classList.add('fade-in');
        
        return postElement;
    }
    
    setupCommentsSection(postElement, post) {
        const commentsSection = postElement.querySelector('.comments-section');
        const commentsHeader = postElement.querySelector('.comments-header');
        const toggleCommentsBtn = postElement.querySelector('.toggle-comments-btn');
        const commentsList = postElement.querySelector('.comments-list');
        
        if (!post.comments || post.comments.total_comments === 0) {
            commentsSection.style.display = 'none';
            return;
        }
        
        // Update comments header
        const commentsTitle = commentsHeader.querySelector('h3');
        commentsTitle.innerHTML = `<i class="fas fa-comments"></i> Comments (${post.comments.total_comments})`;
        
        // Add toggle functionality
        toggleCommentsBtn.addEventListener('click', () => {
            commentsList.classList.toggle('visible');
            toggleCommentsBtn.classList.toggle('active');
            
            if (commentsList.classList.contains('visible')) {
                commentsList.classList.add('slide-down');
            }
        });
        
        // Render comments
        this.renderComments(commentsList, post.comments.comments);
    }
    
    renderComments(container, comments) {
        container.innerHTML = '';
        
        if (!comments || comments.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No comments available</p>';
            return;
        }
        
        comments.forEach(comment => {
            const commentElement = this.createCommentElement(comment);
            container.appendChild(commentElement);
        });
    }
    
    createCommentElement(comment) {
        const template = document.getElementById('comment-template');
        const commentElement = template.content.cloneNode(true);
        
        // Fill in comment data
        const authorElement = commentElement.querySelector('.author-name');
        const timeElement = commentElement.querySelector('.comment-time');
        const messageElement = commentElement.querySelector('.comment-message');
        const idElement = commentElement.querySelector('.comment-id span');
        
        authorElement.textContent = comment.author_name || comment.from?.name || 'Unknown Author';
        timeElement.textContent = this.formatDate(comment.created_time);
        messageElement.textContent = comment.message || 'No message content';
        idElement.textContent = comment.comment_id || comment.id || 'Unknown';
        
        return commentElement;
    }
    
    formatDate(dateString) {
        if (!dateString || dateString === 'Unknown') {
            return 'Unknown date';
        }
        
        try {
            const date = new Date(dateString);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString;
        }
    }
    
    showLoading(show) {
        const loading = document.getElementById('loading');
        const container = document.getElementById('posts-container');
        
        if (show) {
            loading.style.display = 'flex';
            container.style.display = 'none';
        } else {
            loading.style.display = 'none';
            container.style.display = 'block';
        }
    }
    
    showError(message) {
        const errorElement = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        
        errorText.textContent = message;
        errorElement.style.display = 'block';
        
        // Hide other elements
        document.getElementById('loading').style.display = 'none';
        document.getElementById('posts-container').style.display = 'none';
        document.getElementById('no-results').style.display = 'none';
    }
}

// Utility functions
const utils = {
    // Debounce function for search
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Format numbers with commas
    formatNumber(num) {
        return num.toLocaleString();
    },
    
    // Truncate text
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
};

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Facebook Posts & Comments Dashboard...');
    
    // Initialize the posts display
    window.postsDisplay = new PostsDisplay();
    
    console.log('Dashboard initialized successfully!');
});

// Error handling for uncaught errors
window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error);
    
    const errorElement = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    if (errorElement && errorText) {
        errorText.textContent = 'An unexpected error occurred. Please refresh the page.';
        errorElement.style.display = 'block';
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});
