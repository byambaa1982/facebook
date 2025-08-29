#!/usr/bin/env python3
"""
Display Routes for Posts and Comments
=====================================

This module provides routes to display posts and their associated comments
from the unqlite database in a user-friendly interface.
"""

from flask import Blueprint, render_template, jsonify, request
from routes.comment import get_posts_from_db, get_comments_from_db, get_unqlite_db, get_facebook_apps, get_post_comments_from_facebook, store_comments_in_db
import json
from datetime import datetime

display_bp = Blueprint('display', __name__)

def fetch_and_store_comments_for_post(facebook_post_id):
    """Fetch fresh comments from Facebook API and store them in database"""
    try:
        # Get Facebook apps
        apps = get_facebook_apps()
        if not apps:
            return {'success': False, 'error': 'No Facebook apps configured'}
        
        app = apps[0]  # Use first app
        page_id = app.get('page_id')
        access_token = app.get('password')
        
        if not page_id or not access_token:
            return {'success': False, 'error': 'Facebook app credentials incomplete'}
        
        # Fetch comments from Facebook API
        result = get_post_comments_from_facebook(page_id, access_token, facebook_post_id, limit=50)
        
        if 'error' in result:
            return {'success': False, 'error': result['error'].get('message', 'Unknown Facebook API error')}
        
        comments_data = result.get('data', [])
        
        # Find the corresponding content_id from our database
        posts = get_posts_from_db()
        content_id = None
        for post in posts:
            if post.get('facebook_post_id') == facebook_post_id:
                content_id = post.get('id')
                break
        
        if not content_id:
            return {'success': False, 'error': 'Post not found in local database'}
        
        # Store comments in database
        if store_comments_in_db(facebook_post_id, content_id, comments_data):
            return {
                'success': True, 
                'new_comments': len(comments_data),
                'message': f'Successfully fetched and stored {len(comments_data)} comments'
            }
        else:
            return {'success': False, 'error': 'Failed to store comments in database'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def enhance_comments_with_sentiment(comments):
    """Enhance comments list with sentiment data"""
    db = get_unqlite_db()
    enhanced_comments = []
    
    try:
        # Build a sentiment lookup dictionary
        sentiment_lookup = {}
        
        for raw_key in db:
            try:
                # Handle different key types
                if isinstance(raw_key, tuple):
                    key_bytes = raw_key[0] if raw_key else b''
                    value_bytes = raw_key[1] if len(raw_key) > 1 else b''
                elif isinstance(raw_key, bytes):
                    key_bytes = raw_key
                    value_bytes = db[raw_key]
                elif isinstance(raw_key, str):
                    key_bytes = raw_key.encode('utf-8')
                    value_bytes = db[raw_key]
                else:
                    key_bytes = str(raw_key).encode('utf-8')
                    value_bytes = db[raw_key]
                
                # Decode key to string
                if hasattr(key_bytes, 'decode'):
                    key_str = key_bytes.decode('utf-8')
                else:
                    key_str = str(key_bytes)
                
                # Process sentiment keys
                if key_str.startswith('sentiment:'):
                    # Decode value
                    if hasattr(value_bytes, 'decode'):
                        value_str = value_bytes.decode('utf-8')
                    else:
                        value_str = str(value_bytes)
                    
                    sentiment_data = json.loads(value_str)
                    comment_id = sentiment_data.get('comment_id')
                    
                    if comment_id:
                        sentiment_lookup[comment_id] = sentiment_data
                        
            except Exception as e:
                continue
        
        # Enhance comments with sentiment data
        for comment in comments:
            enhanced_comment = comment.copy()
            comment_id = comment.get('id') or comment.get('comment_id')
            
            if comment_id and comment_id in sentiment_lookup:
                enhanced_comment['sentiment'] = sentiment_lookup[comment_id]
            
            enhanced_comments.append(enhanced_comment)
            
    except Exception as e:
        print(f"Error enhancing comments with sentiment: {e}")
        return comments  # Return original comments if error
    finally:
        db.close()
    
    return enhanced_comments

@display_bp.route('/display')
def display_posts():
    """Display the main page showing all posts and comments"""
    return render_template('display.html')

@display_bp.route('/api/posts-with-comments')
def get_posts_with_comments():
    """API endpoint to get all posts with their comments"""
    try:
        # Get all posts from database
        posts = get_posts_from_db()
        
        posts_with_comments = []
        
        for post in posts:
            post_id = post.get('id')
            facebook_post_id = post.get('facebook_post_id')
            
            # Get comments for this post
            comments_data = None
            if facebook_post_id:
                comments_data = get_comments_from_db(post_id, facebook_post_id)
            
            # Build post data with comments
            post_data = {
                'id': post_id,
                'title': post.get('title', 'Untitled'),
                'content': post.get('content', 'No content'),
                'facebook_post_id': facebook_post_id,
                'posted_to_facebook': post.get('posted_to_facebook', False),
                'created_at': post.get('created_at', 'Unknown'),
                'comments': {
                    'total_comments': 0,
                    'comments': []
                }
            }
            
            if comments_data:
                # Enhance comments with sentiment data
                enhanced_comments = enhance_comments_with_sentiment(comments_data.get('comments', []))
                comments_data['comments'] = enhanced_comments
                post_data['comments'] = comments_data
            
            posts_with_comments.append(post_data)
        
        return jsonify({
            'success': True,
            'total_posts': len(posts_with_comments),
            'posts': posts_with_comments
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'posts': []
        }), 500

@display_bp.route('/api/database-stats')
def get_database_stats():
    """Get statistics about the database contents"""
    try:
        db = get_unqlite_db()
        stats = {
            'total_keys': 0,
            'content_keys': 0,
            'comment_keys': 0,
            'other_keys': 0,
            'posts_with_facebook_id': 0,
            'posts_with_comments': 0
        }
        
        # Count different types of keys using the same approach as get_posts_from_db
        for raw_key in db:
            stats['total_keys'] += 1
            try:
                # Handle different key types that unqlite might return
                if isinstance(raw_key, tuple):
                    # UnQLite returns tuples (key, value)
                    key_bytes = raw_key[0] if raw_key else b''
                    value_bytes = raw_key[1] if len(raw_key) > 1 else b''
                elif isinstance(raw_key, bytes):
                    key_bytes = raw_key
                    value_bytes = db[raw_key]  # Get value from database
                elif isinstance(raw_key, str):
                    key_bytes = raw_key.encode('utf-8')
                    value_bytes = db[raw_key]  # Get value from database
                else:
                    # Try to convert to bytes
                    key_bytes = str(raw_key).encode('utf-8')
                    value_bytes = db[raw_key]  # Get value from database
                
                # Decode key to string
                if hasattr(key_bytes, 'decode'):
                    key_str = key_bytes.decode('utf-8')
                else:
                    key_str = str(key_bytes)
                
                if key_str.startswith('content:'):
                    stats['content_keys'] += 1
                    
                    # Check if this content has Facebook post ID
                    try:
                        # Handle value decoding
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        content_data = json.loads(value_str)
                        if content_data.get('facebook_post_id'):
                            stats['posts_with_facebook_id'] += 1
                    except Exception as e:
                        print(f"Error parsing content data for key {key_str}: {e}")
                        
                elif 'comment' in key_str.lower():
                    stats['comment_keys'] += 1
                else:
                    stats['other_keys'] += 1
                    
            except Exception as e:
                print(f"Error processing key {raw_key}: {e}")
                stats['other_keys'] += 1
        
        # Get posts and count those with comments
        try:
            posts = get_posts_from_db()
            for post in posts:
                facebook_post_id = post.get('facebook_post_id')
                if facebook_post_id:
                    comments = get_comments_from_db(post.get('id'), facebook_post_id)
                    if comments and comments.get('total_comments', 0) > 0:
                        stats['posts_with_comments'] += 1
        except Exception as e:
            print(f"Error counting posts with comments: {e}")
        
        db.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'stats': {}
        }), 500

@display_bp.route('/api/post/<post_id>/refresh')
def refresh_post_comments(post_id):
    """Refresh comments for a specific post by fetching from Facebook API"""
    try:
        # Get the post data first to get the facebook_post_id
        posts = get_posts_from_db()
        target_post = None
        
        for post in posts:
            if str(post.get('id')) == str(post_id):
                target_post = post
                break
        
        if not target_post:
            return jsonify({
                'success': False,
                'error': 'Post not found'
            }), 404
        
        facebook_post_id = target_post.get('facebook_post_id')
        
        if not facebook_post_id:
            return jsonify({
                'success': False,
                'error': 'Post has no Facebook post ID'
            }), 400
        
        # Import the function to fetch fresh comments from Facebook API
        try:
            # Fetch fresh comments from Facebook API
            result = fetch_and_store_comments_for_post(facebook_post_id)
            
            if result.get('success'):
                # Get the updated comments from database
                comments_data = get_comments_from_db(post_id, facebook_post_id)
                
                return jsonify({
                    'success': True,
                    'message': 'Comments refreshed successfully',
                    'comments': comments_data or {'total_comments': 0, 'comments': []},
                    'fetched_count': result.get('new_comments', 0)
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Failed to fetch comments')
                }), 500
                
        except Exception as e:
            # Fallback: just return current comments from database
            comments_data = get_comments_from_db(post_id, facebook_post_id)
            return jsonify({
                'success': True,
                'message': 'Returned cached comments (refresh service error)',
                'comments': comments_data or {'total_comments': 0, 'comments': []},
                'fetched_count': 0,
                'error': str(e)
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@display_bp.route('/api/post/<post_id>/comments')
def get_post_comments(post_id):
    """Get comments for a specific post"""
    try:
        facebook_post_id = request.args.get('facebook_post_id')
        
        if not facebook_post_id:
            return jsonify({
                'success': False,
                'error': 'Facebook post ID is required'
            }), 400
        
        comments_data = get_comments_from_db(post_id, facebook_post_id)
        
        if comments_data:
            return jsonify({
                'success': True,
                'comments': comments_data
            })
        else:
            return jsonify({
                'success': True,
                'comments': {
                    'total_comments': 0,
                    'comments': []
                }
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@display_bp.route('/api/search')
def search_posts():
    """Search posts by title or content"""
    try:
        query = request.args.get('q', '').lower()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        posts = get_posts_from_db()
        matching_posts = []
        
        for post in posts:
            title = post.get('title', '').lower()
            content = post.get('content', '').lower()
            
            if query in title or query in content:
                # Get comments for matching post
                facebook_post_id = post.get('facebook_post_id')
                comments_data = None
                if facebook_post_id:
                    comments_data = get_comments_from_db(post.get('id'), facebook_post_id)
                
                post_data = {
                    'id': post.get('id'),
                    'title': post.get('title', 'Untitled'),
                    'content': post.get('content', 'No content'),
                    'facebook_post_id': facebook_post_id,
                    'posted_to_facebook': post.get('posted_to_facebook', False),
                    'created_at': post.get('created_at', 'Unknown'),
                    'comments': comments_data or {'total_comments': 0, 'comments': []}
                }
                
                matching_posts.append(post_data)
        
        return jsonify({
            'success': True,
            'query': query,
            'total_results': len(matching_posts),
            'posts': matching_posts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@display_bp.route('/api/analyze-sentiment')
def analyze_comments_sentiment():
    """Analyze sentiment of all comments using OpenAI"""
    try:
        # Import the sentiment analyzer
        import sys
        import os
        agents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agents')
        sys.path.append(agents_path)
        
        from review import CommentSentimentAnalyzer
        
        # Get force parameter - default to False so it only analyzes new comments
        force_reanalyze = request.args.get('force', 'false').lower() == 'true'
        
        # Initialize analyzer and run analysis
        analyzer = CommentSentimentAnalyzer()
        results = analyzer.analyze_all_comments(force_reanalyze=force_reanalyze)
        
        # Customize message based on results
        if results['analyzed'] == 0 and results['skipped'] > 0:
            message = f"All {results['skipped']} comments already have sentiment labels"
        elif results['analyzed'] > 0:
            message = f"Sentiment analysis completed! Analyzed {results['analyzed']} new comments"
        else:
            message = "No comments found to analyze"
        
        return jsonify({
            'success': True,
            'message': message,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@display_bp.route('/api/sentiment-stats')
def get_sentiment_statistics():
    """Get sentiment analysis statistics"""
    try:
        db = get_unqlite_db()
        
        stats = {
            'total_analyzed': 0,
            'sentiments': {'positive': 0, 'negative': 0, 'neutral': 0},
            'by_post': {}
        }
        
        try:
            for raw_key in db:
                try:
                    # Handle different key types
                    if isinstance(raw_key, tuple):
                        key_bytes = raw_key[0] if raw_key else b''
                        value_bytes = raw_key[1] if len(raw_key) > 1 else b''
                    elif isinstance(raw_key, bytes):
                        key_bytes = raw_key
                        value_bytes = db[raw_key]
                    elif isinstance(raw_key, str):
                        key_bytes = raw_key.encode('utf-8')
                        value_bytes = db[raw_key]
                    else:
                        key_bytes = str(raw_key).encode('utf-8')
                        value_bytes = db[raw_key]
                    
                    # Decode key to string
                    if hasattr(key_bytes, 'decode'):
                        key_str = key_bytes.decode('utf-8')
                    else:
                        key_str = str(key_bytes)
                    
                    # Process sentiment keys
                    if key_str.startswith('sentiment:'):
                        # Decode value
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        sentiment_data = json.loads(value_str)
                        sentiment = sentiment_data.get('sentiment', 'neutral')
                        
                        stats['total_analyzed'] += 1
                        stats['sentiments'][sentiment] += 1
                        
                        # Extract post info from comment key
                        comment_key = sentiment_data.get('comment_key', '')
                        if comment_key:
                            post_id = sentiment_data.get('content_id', 'unknown')
                            if post_id not in stats['by_post']:
                                stats['by_post'][post_id] = {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0}
                            
                            stats['by_post'][post_id][sentiment] += 1
                            stats['by_post'][post_id]['total'] += 1
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error processing sentiment stats: {e}")
        finally:
            db.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@display_bp.route('/api/comment/<comment_id>/sentiment')
def get_comment_sentiment(comment_id):
    """Get sentiment analysis for a specific comment"""
    try:
        db = get_unqlite_db()
        
        try:
            # Search for sentiment data for this comment
            for raw_key in db:
                try:
                    # Handle different key types
                    if isinstance(raw_key, tuple):
                        key_bytes = raw_key[0] if raw_key else b''
                        value_bytes = raw_key[1] if len(raw_key) > 1 else b''
                    elif isinstance(raw_key, bytes):
                        key_bytes = raw_key
                        value_bytes = db[raw_key]
                    elif isinstance(raw_key, str):
                        key_bytes = raw_key.encode('utf-8')
                        value_bytes = db[raw_key]
                    else:
                        key_bytes = str(raw_key).encode('utf-8')
                        value_bytes = db[raw_key]
                    
                    # Decode key to string
                    if hasattr(key_bytes, 'decode'):
                        key_str = key_bytes.decode('utf-8')
                    else:
                        key_str = str(key_bytes)
                    
                    # Check if this is a sentiment key for our comment
                    if key_str.startswith('sentiment:') and comment_id in key_str:
                        # Decode value
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        sentiment_data = json.loads(value_str)
                        
                        # Verify this is the right comment
                        if sentiment_data.get('comment_id') == comment_id:
                            return jsonify({
                                'success': True,
                                'sentiment': sentiment_data
                            })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error searching for sentiment: {e}")
        finally:
            db.close()
        
        # No sentiment found
        return jsonify({
            'success': True,
            'sentiment': None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@display_bp.route('/api/reply-to-comments')
def reply_to_comments():
    """Automatically reply to positive and neutral comments"""
    try:
        # Import the reply agent
        import sys
        import os
        agents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agents')
        sys.path.append(agents_path)
        
        from reply import CommentReplyAgent
        
        # Get max_replies parameter
        max_replies = int(request.args.get('max_replies', 10))
        
        # Initialize agent and run replies
        agent = CommentReplyAgent()
        results = agent.reply_to_comments(max_replies=max_replies)
        
        # Customize message based on results
        if results['replied'] == 0 and results['total'] == 0:
            message = "No comments found that need replies"
        elif results['replied'] == 0 and results['total'] > 0:
            message = f"Found {results['total']} comments but encountered errors posting replies"
        else:
            message = f"Successfully replied to {results['replied']} comments!"
        
        return jsonify({
            'success': True,
            'message': message,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@display_bp.route('/api/reply-stats')
def get_reply_statistics():
    """Get reply statistics"""
    try:
        db = get_unqlite_db()
        
        stats = {
            'total_replies': 0,
            'reply_types': {'question': 0, 'compliment': 0, 'general': 0},
            'by_post': {}
        }
        
        try:
            for raw_key in db:
                try:
                    # Handle different key types
                    if isinstance(raw_key, tuple):
                        key_bytes = raw_key[0] if raw_key else b''
                        value_bytes = raw_key[1] if len(raw_key) > 1 else b''
                    elif isinstance(raw_key, bytes):
                        key_bytes = raw_key
                        value_bytes = db[raw_key]
                    elif isinstance(raw_key, str):
                        key_bytes = raw_key.encode('utf-8')
                        value_bytes = db[raw_key]
                    else:
                        key_bytes = str(raw_key).encode('utf-8')
                        value_bytes = db[raw_key]
                    
                    # Decode key to string
                    if hasattr(key_bytes, 'decode'):
                        key_str = key_bytes.decode('utf-8')
                    else:
                        key_str = str(key_bytes)
                    
                    # Process reply keys
                    if key_str.startswith('reply:'):
                        # Decode value
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        reply_data = json.loads(value_str)
                        reply_type = reply_data.get('reply_type', 'general')
                        
                        stats['total_replies'] += 1
                        stats['reply_types'][reply_type] += 1
                        
                        # Extract post info from comment key
                        comment_key = reply_data.get('comment_key', '')
                        if comment_key:
                            content_id = reply_data.get('comment_key', '').split(':')[1] if ':' in comment_key else 'unknown'
                            if content_id not in stats['by_post']:
                                stats['by_post'][content_id] = {'question': 0, 'compliment': 0, 'general': 0, 'total': 0}
                            
                            stats['by_post'][content_id][reply_type] += 1
                            stats['by_post'][content_id]['total'] += 1
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error processing reply stats: {e}")
        finally:
            db.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
