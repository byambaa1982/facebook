#!/usr/bin/env python3
"""
Comment Reply Agent
===================

This module automatically replies to positive and neutral comments on Facebook posts.
It uses OpenAI to generate appropriate responses and tracks which comments have been replied to.
"""

import sys
import os
import json
from datetime import datetime
from openai import OpenAI

# Add parent directory to path to import routes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.comment import get_unqlite_db, get_facebook_apps, reply_to_facebook_comment

class CommentReplyAgent:
    def __init__(self):
        """Initialize the comment reply agent with OpenAI client"""
        self.client = None
        self.facebook_apps = []
        self.load_openai_config()
        self.load_facebook_config()
    
    def load_openai_config(self):
        """Load OpenAI API configuration"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        
        try:
            with open(config_path, "r") as file:
                config = json.load(file)
                api_key = config.get("openai_api_key")
                
                if api_key:
                    self.client = OpenAI(api_key=api_key)
                    print("✅ OpenAI client initialized successfully")
                else:
                    print("❌ No OpenAI API key found in config.json")
                    
        except FileNotFoundError:
            print(f"❌ Config file not found: {config_path}")
        except Exception as e:
            print(f"❌ Error loading config: {e}")
    
    def load_facebook_config(self):
        """Load Facebook app configuration"""
        try:
            self.facebook_apps = get_facebook_apps()
            if self.facebook_apps:
                print(f"✅ Loaded {len(self.facebook_apps)} Facebook app(s)")
            else:
                print("❌ No Facebook apps configured")
        except Exception as e:
            print(f"❌ Error loading Facebook apps: {e}")
    
    def classify_comment_type(self, comment_text):
        """
        Classify if a comment is a question, compliment, or general comment
        
        Args:
            comment_text (str): The comment text to classify
            
        Returns:
            dict: Contains comment type and suggested reply
        """
        if not self.client:
            return {"type": "general", "error": "OpenAI client not initialized"}
        
        if not comment_text or not comment_text.strip():
            return {"type": "general", "error": "Empty comment"}
        
        try:
            prompt = f"""
            Analyze this comment and determine its type and generate an appropriate reply:

            Comment: "{comment_text}"

            1. First, classify the comment as one of these types:
            - "question": if it asks something or seeks information
            - "compliment": if it praises, appreciates, or gives positive feedback
            - "general": for other neutral comments

            2. Then generate a brief, friendly reply (max 50 words) that:
            - For questions: provides a helpful answer or asks for clarification
            - For compliments: shows appreciation and gratitude
            - For general: acknowledges the comment positively

            Respond in this exact JSON format:
            {{
                "type": "question|compliment|general",
                "reply": "your suggested reply here"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful social media manager. Generate friendly, professional replies to comments. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            reply_data = json.loads(response.choices[0].message.content.strip())
            
            # Validate the response
            if "type" in reply_data and "reply" in reply_data:
                return {
                    "type": reply_data["type"],
                    "reply": reply_data["reply"],
                    "generated_at": datetime.now().isoformat()
                }
            else:
                return {
                    "type": "general",
                    "reply": "Thank you for your comment! 😊",
                    "error": "Invalid response format",
                    "generated_at": datetime.now().isoformat()
                }
                
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "type": "general",
                "reply": "Thank you for your comment! 😊",
                "error": "JSON parsing failed",
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Error classifying comment: {e}")
            return {
                "type": "general",
                "reply": "Thank you for your comment! 😊",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def get_comments_to_reply(self):
        """
        Get all positive and neutral comments that haven't been replied to yet
        
        Returns:
            list: List of comments that need replies
        """
        db = get_unqlite_db()
        comments_to_reply = []
        replied_comments = set()
        
        try:
            # First, get all replied comment IDs
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
                    
                    # Collect replied comment IDs
                    if key_str.startswith('reply:'):
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        reply_data = json.loads(value_str)
                        comment_id = reply_data.get('comment_id')
                        if comment_id:
                            replied_comments.add(comment_id)
                            
                except Exception as e:
                    continue
            
            # Now get sentiment data for positive and neutral comments
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
                    
                    # Process sentiment keys for positive and neutral comments
                    if key_str.startswith('sentiment:'):
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        sentiment_data = json.loads(value_str)
                        sentiment = sentiment_data.get('sentiment', 'neutral')
                        comment_id = sentiment_data.get('comment_id')
                        
                        # Only include positive and neutral comments that haven't been replied to
                        if sentiment in ['positive', 'neutral'] and comment_id not in replied_comments:
                            comments_to_reply.append({
                                'comment_id': comment_id,
                                'comment_key': sentiment_data.get('comment_key'),
                                'message': sentiment_data.get('message', ''),
                                'author_name': sentiment_data.get('author_name', 'Unknown'),
                                'created_time': sentiment_data.get('created_time'),
                                'sentiment': sentiment,
                                'sentiment_data': sentiment_data
                            })
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error retrieving comments to reply: {e}")
        finally:
            db.close()
        
        return comments_to_reply
    
    def post_reply_to_facebook(self, comment_id, reply_text):
        """
        Post a reply to a Facebook comment
        
        Args:
            comment_id (str): The Facebook comment ID
            reply_text (str): The reply text to post
            
        Returns:
            dict: Result of the reply attempt
        """
        if not self.facebook_apps:
            return {'success': False, 'error': 'No Facebook apps configured'}
        
        app = self.facebook_apps[0]  # Use first app
        access_token = app.get('password')
        
        if not access_token:
            return {'success': False, 'error': 'No access token available'}
        
        try:
            result = reply_to_facebook_comment(access_token, comment_id, reply_text)
            
            if 'error' in result:
                return {
                    'success': False, 
                    'error': result['error'].get('message', 'Unknown Facebook API error')
                }
            else:
                return {
                    'success': True,
                    'reply_id': result.get('id'),
                    'message': 'Reply posted successfully'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_comment_from_db(self, comment_id, comment_key):
        """
        Delete a comment and its related data from the database
        
        Args:
            comment_id (str): The Facebook comment ID
            comment_key (str): The database key for the comment
        """
        db = get_unqlite_db()
        deleted_keys = []
        
        try:
            # Find and delete all keys related to this comment
            keys_to_delete = []
            
            for raw_key in db:
                try:
                    # Handle different key types
                    if isinstance(raw_key, tuple):
                        key_bytes = raw_key[0] if raw_key else b''
                    elif isinstance(raw_key, bytes):
                        key_bytes = raw_key
                    elif isinstance(raw_key, str):
                        key_bytes = raw_key.encode('utf-8')
                    else:
                        key_bytes = str(raw_key).encode('utf-8')
                    
                    # Decode key to string
                    if hasattr(key_bytes, 'decode'):
                        key_str = key_bytes.decode('utf-8')
                    else:
                        key_str = str(key_bytes)
                    
                    # Collect keys related to this comment
                    if comment_id in key_str:
                        keys_to_delete.append(key_str)
                        
                except Exception as e:
                    continue
            
            # Delete the collected keys
            for key in keys_to_delete:
                try:
                    if key.encode('utf-8') in db:
                        del db[key.encode('utf-8')]
                        deleted_keys.append(key)
                    elif key in db:
                        del db[key]
                        deleted_keys.append(key)
                except Exception as e:
                    print(f"Error deleting key {key}: {e}")
            
            db.commit()
            
            if deleted_keys:
                print(f"🗑️ Deleted {len(deleted_keys)} database entries for comment {comment_id}")
                for key in deleted_keys:
                    print(f"   - {key}")
            
            return len(deleted_keys) > 0
            
        except Exception as e:
            print(f"Error deleting comment from database: {e}")
            return False
        finally:
            db.close()
    
    def is_comment_not_found_error(self, error_result):
        """
        Check if the error indicates the comment doesn't exist on Facebook
        
        Args:
            error_result (dict): The error result from Facebook API
            
        Returns:
            bool: True if comment doesn't exist, False otherwise
        """
        if not isinstance(error_result.get('error'), dict):
            return False
        
        error_message = error_result['error'].get('message', '').lower()
        error_code = error_result['error'].get('code')
        error_subcode = error_result['error'].get('error_subcode')
        
        # Check for common "not found" indicators
        not_found_indicators = [
            'does not exist',
            'cannot be loaded',
            'missing permissions',
            'does not support this operation'
        ]
        
        # Facebook error codes that typically indicate missing/deleted content
        not_found_codes = [100, 803]  # 100 = Invalid parameter, 803 = Some of the aliases you requested do not exist
        not_found_subcodes = [33]     # 33 = Object does not exist
        
        message_indicates_not_found = any(indicator in error_message for indicator in not_found_indicators)
        code_indicates_not_found = error_code in not_found_codes or error_subcode in not_found_subcodes
        
        return message_indicates_not_found or code_indicates_not_found

    def store_reply_in_db(self, comment_id, comment_key, reply_data):
        """
        Store reply information in the database
        
        Args:
            comment_id (str): The Facebook comment ID
            comment_key (str): The database key for the comment
            reply_data (dict): The reply information
        """
        db = get_unqlite_db()
        
        try:
            # Create a reply key
            reply_key = f"reply:{comment_key}:{comment_id}"
            
            # Store reply data
            db[reply_key] = json.dumps(reply_data)
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error storing reply: {e}")
            return False
        finally:
            db.close()
    
    def reply_to_comments(self, max_replies=10):
        """
        Reply to positive and neutral comments that haven't been replied to
        
        Args:
            max_replies (int): Maximum number of replies to post in one run
            
        Returns:
            dict: Summary of reply results
        """
        print("🤖 Starting automated comment replies...")
        print("=" * 50)
        
        comments = self.get_comments_to_reply()
        
        if not comments:
            print("❌ No comments found that need replies")
            return {"total": 0, "replied": 0, "skipped": 0, "errors": 0}
        
        print(f"📊 Found {len(comments)} comments to reply to")
        
        # Limit the number of replies per run
        comments_to_process = comments[:max_replies]
        if len(comments) > max_replies:
            print(f"⚠️ Limiting to {max_replies} replies this run (total: {len(comments)})")
        
        stats = {
            "total": len(comments),
            "processed": len(comments_to_process),
            "replied": 0,
            "skipped": 0,
            "cleaned_up": 0,
            "errors": 0,
            "reply_types": {"question": 0, "compliment": 0, "general": 0}
        }
        
        for i, comment in enumerate(comments_to_process, 1):
            comment_id = comment['comment_id']
            message = comment['message']
            author_name = comment['author_name']
            sentiment = comment['sentiment']
            
            print(f"\n[{i}/{len(comments_to_process)}] Processing comment by {author_name}")
            print(f"💭 Comment ({sentiment}): \"{message[:50]}{'...' if len(message) > 50 else ''}\"")
            
            # Generate reply using AI
            reply_info = self.classify_comment_type(message)
            
            if "error" in reply_info:
                print(f"❌ Error generating reply: {reply_info['error']}")
                stats["errors"] += 1
                continue
            
            reply_type = reply_info.get('type', 'general')
            reply_text = reply_info.get('reply', 'Thank you for your comment! 😊')
            
            print(f"🎯 Classified as: {reply_type}")
            print(f"💬 Generated reply: \"{reply_text}\"")
            
            # Post reply to Facebook
            facebook_result = self.post_reply_to_facebook(comment_id, reply_text)
            
            if facebook_result['success']:
                print(f"✅ Reply posted to Facebook successfully")
                
                # Store reply information in database
                reply_storage = {
                    "comment_id": comment_id,
                    "comment_key": comment['comment_key'],
                    "original_message": message,
                    "author_name": author_name,
                    "sentiment": sentiment,
                    "reply_type": reply_type,
                    "reply_text": reply_text,
                    "facebook_reply_id": facebook_result.get('reply_id'),
                    "replied_at": datetime.now().isoformat(),
                    **reply_info
                }
                
                if self.store_reply_in_db(comment_id, comment['comment_key'], reply_storage):
                    print(f"✅ Reply information stored in database")
                    stats["replied"] += 1
                    stats["reply_types"][reply_type] += 1
                else:
                    print(f"⚠️ Reply posted but failed to store in database")
                    stats["replied"] += 1
                    stats["reply_types"][reply_type] += 1
                    
            else:
                # Check if this is a "comment not found" error
                if 'error' in facebook_result and self.is_comment_not_found_error({'error': {'message': facebook_result['error']}}):
                    print(f"🗑️ Comment not found on Facebook - cleaning up database")
                    
                    if self.delete_comment_from_db(comment_id, comment['comment_key']):
                        print(f"✅ Orphaned comment data cleaned up successfully")
                        stats["cleaned_up"] += 1
                    else:
                        print(f"❌ Failed to clean up orphaned comment data")
                        stats["errors"] += 1
                else:
                    print(f"❌ Failed to post reply: {facebook_result['error']}")
                    stats["errors"] += 1
        
        print("\n" + "=" * 50)
        print("📈 REPLY SUMMARY")
        print("=" * 50)
        print(f"Total comments found: {stats['total']}")
        print(f"Comments processed: {stats['processed']}")
        print(f"Successfully replied: {stats['replied']}")
        print(f"Cleaned up orphaned: {stats['cleaned_up']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nReply types:")
        print(f"  Questions answered: {stats['reply_types']['question']}")
        print(f"  Compliments appreciated: {stats['reply_types']['compliment']}")
        print(f"  General responses: {stats['reply_types']['general']}")
        
        return stats

    def cleanup_orphaned_comments(self):
        """
        Check all comments in database and remove those that no longer exist on Facebook
        
        Returns:
            dict: Summary of cleanup results
        """
        print("🧹 Starting orphaned comment cleanup...")
        print("=" * 50)
        
        # Get all comments with sentiment data
        all_comments = self.get_all_comments_from_sentiment_db()
        
        if not all_comments:
            print("❌ No comments found in database")
            return {"total": 0, "checked": 0, "deleted": 0, "errors": 0}
        
        print(f"📊 Found {len(all_comments)} comments to check")
        
        stats = {
            "total": len(all_comments),
            "checked": 0,
            "deleted": 0,
            "errors": 0
        }
        
        for i, comment in enumerate(all_comments, 1):
            comment_id = comment['comment_id']
            comment_key = comment['comment_key']
            
            print(f"\n[{i}/{len(all_comments)}] Checking comment {comment_id}")
            
            # Try to reply with empty string to test if comment exists
            test_result = self.post_reply_to_facebook(comment_id, "")
            stats["checked"] += 1
            
            if not test_result['success'] and self.is_comment_not_found_error({'error': {'message': test_result['error']}}):
                print(f"🗑️ Comment not found on Facebook - deleting from database")
                
                if self.delete_comment_from_db(comment_id, comment_key):
                    print(f"✅ Orphaned comment deleted successfully")
                    stats["deleted"] += 1
                else:
                    print(f"❌ Failed to delete orphaned comment")
                    stats["errors"] += 1
            else:
                print(f"✅ Comment exists on Facebook")
        
        print("\n" + "=" * 50)
        print("📈 CLEANUP SUMMARY")
        print("=" * 50)
        print(f"Total comments: {stats['total']}")
        print(f"Comments checked: {stats['checked']}")
        print(f"Orphaned comments deleted: {stats['deleted']}")
        print(f"Errors: {stats['errors']}")
        
        return stats
    
    def get_all_comments_from_sentiment_db(self):
        """Get all comments that have sentiment data"""
        db = get_unqlite_db()
        comments = []
        
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
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        sentiment_data = json.loads(value_str)
                        comment_id = sentiment_data.get('comment_id')
                        
                        if comment_id:
                            comments.append({
                                'comment_id': comment_id,
                                'comment_key': sentiment_data.get('comment_key'),
                                'message': sentiment_data.get('message', ''),
                                'sentiment': sentiment_data.get('sentiment'),
                                'sentiment_data': sentiment_data
                            })
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error retrieving comments: {e}")
        finally:
            db.close()
        
        return comments

def main():
    """Main function to run comment reply agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Reply to Facebook comments automatically")
    parser.add_argument("--max-replies", type=int, default=10, help="Maximum number of replies to post")
    parser.add_argument("--test", action="store_true", help="Test reply generation without posting")
    parser.add_argument("--cleanup", action="store_true", help="Clean up orphaned comments from database")
    
    args = parser.parse_args()
    
    agent = CommentReplyAgent()
    
    if args.test:
        # Test with sample comments
        test_comments = [
            "How does this work? Can you explain more?",
            "This is amazing! Great job on this post!",
            "Thanks for sharing this information."
        ]
        
        print("🧪 Testing reply generation with sample comments:")
        for comment in test_comments:
            result = agent.classify_comment_type(comment)
            print(f"Comment: \"{comment}\"")
            print(f"Type: {result.get('type', 'unknown')}")
            print(f"Reply: \"{result.get('reply', 'N/A')}\"")
            print("-" * 40)
    elif args.cleanup:
        # Clean up orphaned comments
        agent.cleanup_orphaned_comments()
    else:
        # Reply to actual comments
        agent.reply_to_comments(max_replies=args.max_replies)

if __name__ == "__main__":
    main()
