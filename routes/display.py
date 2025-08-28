#!/usr/bin/env python3
"""
Display Routes for Posts and Comments
=====================================

This module provides routes to display posts and their associated comments
from the unqlite database in a user-friendly interface.
"""

from flask import Blueprint, render_template, jsonify, request
from routes.comment import get_posts_from_db, get_comments_from_db, get_unqlite_db
import json
from datetime import datetime

display_bp = Blueprint('display', __name__)

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
        
        # Count different types of keys
        for key in db:
            stats['total_keys'] += 1
            try:
                if hasattr(key, 'decode'):
                    key_str = key.decode('utf-8')
                else:
                    key_str = str(key)
                
                if key_str.startswith('content:'):
                    stats['content_keys'] += 1
                    
                    # Check if this content has Facebook post ID
                    try:
                        value = db[key]
                        if hasattr(value, 'decode'):
                            content_data = json.loads(value.decode('utf-8'))
                            if content_data.get('facebook_post_id'):
                                stats['posts_with_facebook_id'] += 1
                    except:
                        pass
                        
                elif 'comment' in key_str.lower():
                    stats['comment_keys'] += 1
                else:
                    stats['other_keys'] += 1
                    
            except Exception as e:
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
        except:
            pass
        
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
