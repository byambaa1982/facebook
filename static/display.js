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
        
        // Sentiment analysis buttons
        document.getElementById('analyze-sentiment-btn').addEventListener('click', () => {
            this.analyzeSentiment();
        });
        
        document.getElementById('show-sentiment-stats').addEventListener('click', () => {
            this.showSentimentStats();
        });
        
        // Reply buttons
        document.getElementById('reply-to-comments-btn').addEventListener('click', () => {
            this.replyToComments();
        });
        
        document.getElementById('show-reply-stats').addEventListener('click', () => {
            this.showReplyStats();
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
        const refreshBtn = postElement.querySelector('.refresh-btn');
        const postDetails = postElement.querySelector('.post-details');
        
        toggleBtn.addEventListener('click', () => {
            postDetails.classList.toggle('visible');
            toggleBtn.classList.toggle('active');
        });
        
        refreshBtn.addEventListener('click', () => {
            this.refreshPostComments(post.id, refreshBtn, postElement);
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
        const sentimentElement = commentElement.querySelector('.comment-sentiment');
        
        authorElement.textContent = comment.author_name || comment.from?.name || 'Unknown Author';
        timeElement.textContent = this.formatDate(comment.created_time);
        messageElement.textContent = comment.message || 'No message content';
        idElement.textContent = comment.comment_id || comment.id || 'Unknown';
        
        // Display sentiment if available
        if (comment.sentiment) {
            this.displayCommentSentiment(sentimentElement, comment.sentiment);
        }
        
        return commentElement;
    }
    
    displayCommentSentiment(sentimentElement, sentimentData) {
        const sentimentLabel = sentimentElement.querySelector('.sentiment-label');
        const sentiment = sentimentData.sentiment || 'neutral';
        
        sentimentLabel.textContent = sentiment;
        sentimentLabel.className = `sentiment-label ${sentiment}`;
        sentimentElement.style.display = 'block';
    }
    
    async refreshPostComments(postId, refreshBtn, postElement) {
        try {
            // Show loading state
            refreshBtn.classList.add('loading');
            refreshBtn.disabled = true;
            refreshBtn.title = 'Refreshing comments...';
            
            // Call refresh API
            const response = await fetch(`/api/post/${postId}/refresh`);
            const data = await response.json();
            
            if (data.success) {
                // Update the comments section with fresh data
                const commentsSection = postElement.querySelector('.comments-section');
                const commentsList = postElement.querySelector('.comments-list');
                const commentsHeader = postElement.querySelector('.comments-header');
                const commentsBadge = postElement.querySelector('.comments-badge');
                
                if (data.comments && data.comments.total_comments > 0) {
                    // Show comments section if it was hidden
                    commentsSection.style.display = 'block';
                    
                    // Update comments header
                    const commentsTitle = commentsHeader.querySelector('h3');
                    commentsTitle.innerHTML = `<i class="fas fa-comments"></i> Comments (${data.comments.total_comments})`;
                    
                    // Update comments badge
                    if (commentsBadge) {
                        commentsBadge.style.display = 'flex';
                        commentsBadge.querySelector('.comment-count').textContent = data.comments.total_comments;
                    }
                    
                    // Re-render comments
                    this.renderComments(commentsList, data.comments.comments);
                    
                    // Show success message
                    if (data.fetched_count > 0) {
                        this.showTemporaryMessage(refreshBtn, `Refreshed! ${data.fetched_count} new comments`, 'success');
                    } else {
                        this.showTemporaryMessage(refreshBtn, 'Comments up to date', 'info');
                    }
                } else {
                    // No comments found
                    commentsSection.style.display = 'none';
                    if (commentsBadge) {
                        commentsBadge.style.display = 'none';
                    }
                    this.showTemporaryMessage(refreshBtn, 'No comments found', 'info');
                }
                
            } else {
                this.showTemporaryMessage(refreshBtn, `Error: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error refreshing comments:', error);
            this.showTemporaryMessage(refreshBtn, 'Refresh failed', 'error');
        } finally {
            // Reset button state
            refreshBtn.classList.remove('loading');
            refreshBtn.disabled = false;
            refreshBtn.title = 'Refresh post comments';
        }
    }
    
    showTemporaryMessage(button, message, type = 'info') {
        const originalTitle = button.title;
        const originalColor = button.style.borderColor;
        
        // Update button appearance based on message type
        button.title = message;
        
        switch (type) {
            case 'success':
                button.style.borderColor = '#28a745';
                button.style.color = '#28a745';
                break;
            case 'error':
                button.style.borderColor = '#dc3545';
                button.style.color = '#dc3545';
                break;
            case 'info':
                button.style.borderColor = '#17a2b8';
                button.style.color = '#17a2b8';
                break;
        }
        
        // Reset after 3 seconds
        setTimeout(() => {
            button.title = originalTitle;
            button.style.borderColor = originalColor;
            button.style.color = '';
        }, 3000);
    }

    async analyzeSentiment(forceReanalyze = false) {
        const button = document.getElementById('analyze-sentiment-btn');
        const originalText = button.innerHTML;
        
        try {
            // Show loading state
            button.disabled = true;
            button.classList.add('loading');
            button.innerHTML = '<i class="fas fa-brain"></i> Analyzing...';
            
            // Call sentiment analysis API
            const url = `/api/analyze-sentiment${forceReanalyze ? '?force=true' : ''}`;
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                const results = data.results;
                
                // Show appropriate message based on results
                if (results.analyzed === 0 && results.skipped > 0) {
                    this.showNotification(
                        `ℹ️ All ${results.skipped} comments already have sentiment labels`, 
                        'info'
                    );
                } else if (results.analyzed > 0) {
                    this.showNotification(
                        `✅ Analyzed ${results.analyzed} new comments! (${results.skipped} already labeled)`, 
                        'success'
                    );
                    
                    // Automatically show sentiment stats after new analysis
                    setTimeout(() => {
                        this.showSentimentStats();
                    }, 1000);
                } else {
                    this.showNotification(
                        'ℹ️ No comments found to analyze', 
                        'info'
                    );
                }
                
            } else {
                this.showNotification(`❌ Error: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error analyzing sentiment:', error);
            this.showNotification('❌ Failed to analyze sentiment', 'error');
        } finally {
            // Reset button state
            button.disabled = false;
            button.classList.remove('loading');
            button.innerHTML = originalText;
        }
    }
    
    async showSentimentStats() {
        try {
            // Fetch sentiment statistics
            const response = await fetch('/api/sentiment-stats');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.stats;
                
                // Update sentiment stats display
                document.getElementById('sentiment-positive').textContent = stats.sentiments.positive;
                document.getElementById('sentiment-negative').textContent = stats.sentiments.negative;
                document.getElementById('sentiment-neutral').textContent = stats.sentiments.neutral;
                document.getElementById('sentiment-total').textContent = stats.total_analyzed;
                
                // Show sentiment stats section
                const sentimentSection = document.getElementById('sentiment-stats');
                sentimentSection.style.display = 'block';
                
                // Smooth scroll to sentiment stats
                sentimentSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                
                // Add a highlight animation
                sentimentSection.style.animation = 'highlight 2s ease-in-out';
                setTimeout(() => {
                    sentimentSection.style.animation = '';
                }, 2000);
                
            } else {
                this.showNotification(`❌ Error loading sentiment stats: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error fetching sentiment stats:', error);
            this.showNotification('❌ Failed to load sentiment statistics', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        const autoRemove = setTimeout(() => {
            this.removeNotification(notification);
        }, 5000);
        
        // Close button functionality
        notification.querySelector('.notification-close').addEventListener('click', () => {
            clearTimeout(autoRemove);
            this.removeNotification(notification);
        });
        
        // Show with animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
    }
    
    removeNotification(notification) {
        notification.classList.add('hide');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    async replyToComments(maxReplies = 10) {
        const button = document.getElementById('reply-to-comments-btn');
        const originalText = button.innerHTML;
        
        try {
            // Show loading state
            button.disabled = true;
            button.classList.add('loading');
            button.innerHTML = '<i class="fas fa-reply"></i> Replying...';
            
            // Call reply API
            const url = `/api/reply-to-comments?max_replies=${maxReplies}`;
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                const results = data.results;
                
                // Show appropriate message based on results
                if (results.replied === 0 && results.total === 0) {
                    this.showNotification(
                        'ℹ️ No comments found that need replies', 
                        'info'
                    );
                } else if (results.replied > 0) {
                    this.showNotification(
                        `✅ Successfully replied to ${results.replied} comments! (${results.reply_types.question} questions, ${results.reply_types.compliment} compliments, ${results.reply_types.general} general)`, 
                        'success'
                    );
                    
                    // Automatically show reply stats after new replies
                    setTimeout(() => {
                        this.showReplyStats();
                    }, 1000);
                } else {
                    this.showNotification(
                        `⚠️ Found ${results.total} comments but couldn't reply to any`, 
                        'info'
                    );
                }
                
            } else {
                this.showNotification(`❌ Error: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error replying to comments:', error);
            this.showNotification('❌ Failed to reply to comments', 'error');
        } finally {
            // Reset button state
            button.disabled = false;
            button.classList.remove('loading');
            button.innerHTML = originalText;
        }
    }
    
    async showReplyStats() {
        try {
            // Fetch reply statistics
            const response = await fetch('/api/reply-stats');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.stats;
                
                // Update reply stats display
                document.getElementById('reply-questions').textContent = stats.reply_types.question;
                document.getElementById('reply-compliments').textContent = stats.reply_types.compliment;
                document.getElementById('reply-general').textContent = stats.reply_types.general;
                document.getElementById('reply-total').textContent = stats.total_replies;
                
                // Show reply stats section
                const replySection = document.getElementById('reply-stats');
                replySection.style.display = 'block';
                
                // Smooth scroll to reply stats
                replySection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                
                // Add a highlight animation
                replySection.style.animation = 'highlight 2s ease-in-out';
                setTimeout(() => {
                    replySection.style.animation = '';
                }, 2000);
                
            } else {
                this.showNotification(`❌ Error loading reply stats: ${data.error}`, 'error');
            }
            
        } catch (error) {
            console.error('Error fetching reply stats:', error);
            this.showNotification('❌ Failed to load reply statistics', 'error');
        }
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
