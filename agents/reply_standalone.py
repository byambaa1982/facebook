#!/usr/bin/env python3
"""
Facebook Comment Reply Agent (Standalone)

Automatically replies to Facebook comments using OpenAI's GPT models.
Handles comment classification, reply generation, and posting to Facebook.
Includes error handling for orphaned comments and database cleanup.
"""

import os
import json
import unqlite
import traceback
import requests
from datetime import datetime
from openai import OpenAI

class CommentReplyAgent:
    def __init__(self):
        """Initialize the comment reply agent with OpenAI client"""
        self.client = None
        self.facebook_apps = []
        self.setup_openai()
        self.load_facebook_apps()
        
    def setup_openai(self):
        """Setup OpenAI client with API key"""
        try:
            # Try environment variable first
            api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                # Try reading from agents config file
                config_path = os.path.join(os.path.dirname(__file__), 'config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        api_key = config.get('openai_api_key')
                
                # Fallback to routes creds file
                if not api_key:
                    config_path = os.path.join(os.path.dirname(__file__), '..', 'routes', 'creds.json')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            creds = json.load(f)
                            api_key = creds.get('openai_api_key')
            
            if not api_key:
                print("❌ No OpenAI API key found. Please set OPENAI_API_KEY environment variable or add to agents/config.json")
                return
                
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized successfully")
            
        except Exception as e:
            print(f"❌ Error setting up OpenAI client: {e}")
            
    def load_facebook_apps(self):
        """Load Facebook app credentials from creds.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'routes', 'creds.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    creds = json.load(f)
                    
                # Convert data array to facebook_apps format
                if 'data' in creds and isinstance(creds['data'], list):
                    self.facebook_apps = []
                    for app in creds['data']:
                        if 'access_token' in app:
                            self.facebook_apps.append({
                                'app_id': app.get('id'),
                                'access_token': app.get('access_token'),
                                'name': app.get('name')
                            })
                            
                # Also check for page_token format
                elif 'page_token' in creds:
                    self.facebook_apps = [{
                        'app_id': creds.get('page_id'),
                        'access_token': creds.get('page_token')
                    }]
                    
                # Legacy format
                elif 'facebook_apps' in creds:
                    self.facebook_apps = creds['facebook_apps']
                elif 'app_id' in creds and 'access_token' in creds:
                    self.facebook_apps = [{
                        'app_id': creds['app_id'],
                        'access_token': creds['access_token']
                    }]
                    
                print(f"✅ Loaded {len(self.facebook_apps)} Facebook app(s)")
            else:
                print("❌ No Facebook app credentials found in creds.json")
                
        except Exception as e:
            print(f"❌ Error loading Facebook apps: {e}")
            
    def get_database(self):
        """Get UnQLite database connection"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'data.db')
            return unqlite.UnQLite(db_path)
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return None
            
    def classify_comment_type(self, comment_text):
        """Classify comment and generate reply using OpenAI"""
        if not self.client:
            return {"type": "unknown", "reply": "OpenAI not available"}
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a social media assistant helping to classify comments and generate appropriate replies.
                        
                        For each comment, classify it as one of:
                        - "question": If the comment asks something or seeks information
                        - "compliment": If the comment is positive, praising, or appreciative
                        - "neutral": If the comment is informational or neutral
                        - "negative": If the comment is critical, negative, or inappropriate (do not reply to these)
                        
                        If the type is "question", generate a helpful answer.
                        If the type is "compliment", generate a grateful response.
                        If the type is "neutral", generate a friendly acknowledgment.
                        If the type is "negative", do not generate a reply.
                        
                        Keep replies conversational, friendly, and under 280 characters.
                        Return ONLY a JSON object with "type" and "reply" fields."""
                    },
                    {
                        "role": "user",
                        "content": f"Classify this comment and generate a reply: \"{comment_text}\""
                    }
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                return json.loads(result)
            except:
                # Fallback if not valid JSON
                return {"type": "unknown", "reply": "Thank you for your comment!"}
                
        except Exception as e:
            print(f"❌ Error classifying comment: {e}")
            return {"type": "unknown", "reply": "Thank you for your comment!"}
            
    def post_reply_to_facebook(self, comment_id, reply_text):
        """Post a reply to a Facebook comment"""
        if not self.facebook_apps:
            print("❌ No Facebook apps configured")
            return False
            
        # Use first available Facebook app
        facebook_app = self.facebook_apps[0]
        access_token = facebook_app.get('access_token')
        
        if not access_token:
            print("❌ No access token available")
            return False
            
        try:
            # Facebook Graph API endpoint for replying to comments
            url = f"https://graph.facebook.com/v18.0/{comment_id}/comments"
            
            data = {
                'message': reply_text,
                'access_token': access_token
            }
            
            response = requests.post(url, data=data)
            result = response.json()
            
            if response.status_code == 200 and 'id' in result:
                print(f"✅ Reply posted successfully to comment {comment_id}")
                return True
            else:
                print(f"❌ Failed to post reply to comment {comment_id}: {result}")
                
                # Check if it's a "comment not found" error
                if self.is_comment_not_found_error(result):
                    print(f"🧹 Comment {comment_id} no longer exists, will clean up from database")
                    self.delete_comment_from_db(comment_id)
                    
                return False
                
        except Exception as e:
            print(f"❌ Error posting reply to Facebook: {e}")
            return False
            
    def is_comment_not_found_error(self, error_response):
        """Check if the error indicates that the comment was not found"""
        if isinstance(error_response, dict):
            error = error_response.get('error', {})
            # Facebook error code 100 with subcode 33 typically means "object not found"
            if error.get('code') == 100 and error.get('error_subcode') == 33:
                return True
            # Also check for specific error messages
            message = error.get('message', '').lower()
            if 'comment does not exist' in message or 'object does not exist' in message:
                return True
        return False
        
    def delete_comment_from_db(self, comment_id):
        """Delete a comment and related data from the database"""
        db = self.get_database()
        if not db:
            return False
            
        try:
            deleted_count = 0
            
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
                    
                    # Check if this key is related to our comment
                    if (key_str.startswith('comment:') or 
                        key_str.startswith('sentiment:') or 
                        key_str.startswith('reply:')):
                        
                        # Get the value to check if it contains our comment_id
                        try:
                            value_bytes = db[raw_key]
                            if hasattr(value_bytes, 'decode'):
                                value_str = value_bytes.decode('utf-8')
                            else:
                                value_str = str(value_bytes)
                            
                            data = json.loads(value_str)
                            
                            # Check various ways the comment_id might be stored
                            if (data.get('id') == comment_id or 
                                data.get('comment_id') == comment_id or
                                comment_id in str(data)):
                                keys_to_delete.append(raw_key)
                                
                        except (json.JSONDecodeError, Exception):
                            # If we can't parse the value, skip it
                            continue
                            
                except Exception:
                    continue
            
            # Delete the identified keys
            for key in keys_to_delete:
                try:
                    del db[key]
                    deleted_count += 1
                except Exception:
                    continue
                    
            if deleted_count > 0:
                print(f"🗑️ Deleted {deleted_count} database entries for comment {comment_id}")
            else:
                print(f"ℹ️ No database entries found for comment {comment_id}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error deleting comment {comment_id} from database: {e}")
            return False
        finally:
            db.close()
            
    def reply_to_comments(self, max_replies=10):
        """Find and reply to positive/neutral comments that haven't been replied to"""
        if not self.client:
            print("❌ OpenAI client not available")
            return
            
        db = self.get_database()
        if not db:
            return
            
        try:
            replies_posted = 0
            
            # Get existing sentiment analysis and replied comments
            sentiment_data = {}
            replied_comments = set()
            
            # Scan database for sentiment and reply data
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
                    
                    # Decode value
                    if hasattr(value_bytes, 'decode'):
                        value_str = value_bytes.decode('utf-8')
                    else:
                        value_str = str(value_bytes)
                    
                    # Process sentiment data
                    if key_str.startswith('sentiment:'):
                        try:
                            data = json.loads(value_str)
                            comment_id = data.get('comment_id')
                            sentiment = data.get('sentiment')
                            if comment_id and sentiment:
                                sentiment_data[comment_id] = {
                                    'sentiment': sentiment,
                                    'message': data.get('message', ''),
                                    'author_name': data.get('author_name', 'Unknown')
                                }
                        except json.JSONDecodeError:
                            continue
                    
                    # Process reply data
                    elif key_str.startswith('reply:'):
                        try:
                            data = json.loads(value_str)
                            comment_id = data.get('comment_id')
                            if comment_id:
                                replied_comments.add(comment_id)
                        except json.JSONDecodeError:
                            continue
                            
                except Exception:
                    continue
                        
            print(f"📊 Found {len(sentiment_data)} comments with sentiment, {len(replied_comments)} already replied")
            
            # Process comments that need replies
            for comment_id, data in sentiment_data.items():
                if replies_posted >= max_replies:
                    break
                    
                # Skip if already replied
                if comment_id in replied_comments:
                    continue
                    
                # Only reply to positive/neutral
                sentiment = data['sentiment']
                if sentiment not in ['positive', 'neutral']:
                    print(f"⏭️ Skipping comment {comment_id} (sentiment: {sentiment})")
                    continue
                    
                comment_text = data['message']
                if not comment_text:
                    continue
                    
                print(f"🤖 Processing comment {comment_id}: \"{comment_text[:100]}...\"")
                
                # Classify and generate reply
                result = self.classify_comment_type(comment_text)
                comment_type = result.get('type', 'unknown')
                reply_text = result.get('reply', '')
                
                # Don't reply to negative comments
                if comment_type == 'negative':
                    print(f"⏭️ Skipping negative comment {comment_id}")
                    continue
                    
                if not reply_text:
                    print(f"⏭️ No reply generated for comment {comment_id}")
                    continue
                    
                print(f"💬 Generated reply ({comment_type}): \"{reply_text}\"")
                
                # Post reply to Facebook
                success = self.post_reply_to_facebook(comment_id, reply_text)
                
                if success:
                    # Record the reply in database
                    reply_record = {
                        'comment_id': comment_id,
                        'reply_text': reply_text,
                        'comment_type': comment_type,
                        'sentiment': sentiment,
                        'author_name': data['author_name'],
                        'original_message': comment_text,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    reply_key = f"reply:{comment_id}:{int(datetime.now().timestamp())}"
                    db[reply_key] = json.dumps(reply_record)
                    replies_posted += 1
                    
                    print(f"✅ Reply {replies_posted}/{max_replies} posted successfully")
                else:
                    print(f"❌ Failed to post reply to comment {comment_id}")
                    
            print(f"🎉 Completed! Posted {replies_posted} replies out of {max_replies} maximum")
            
        except Exception as e:
            print(f"❌ Error in reply_to_comments: {e}")
            traceback.print_exc()
        finally:
            db.close()
            
    def cleanup_orphaned_comments(self):
        """Clean up comments that no longer exist on Facebook"""
        print("🧹 Starting cleanup of orphaned comments...")
        
        db = self.get_database()
        if not db:
            return
            
        try:
            orphaned_count = 0
            comment_ids = set()
            
            # First pass: collect all comment IDs from the database
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
                    
                    # Look for comment entries
                    if key_str.startswith('comment:'):
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        try:
                            comment_data = json.loads(value_str)
                            comment_id = comment_data.get('id')
                            if comment_id:
                                comment_ids.add(comment_id)
                        except json.JSONDecodeError:
                            continue
                            
                except Exception:
                    continue
            
            print(f"📊 Found {len(comment_ids)} comments in database")
            
            # Second pass: check each comment on Facebook
            for comment_id in comment_ids:
                if self.check_comment_exists(comment_id):
                    print(f"✅ Comment {comment_id} still exists")
                else:
                    print(f"🗑️ Comment {comment_id} no longer exists, cleaning up...")
                    self.delete_comment_from_db(comment_id)
                    orphaned_count += 1
                    
            print(f"🎉 Cleanup completed! Removed {orphaned_count} orphaned comments")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            traceback.print_exc()
        finally:
            db.close()
            
    def check_comment_exists(self, comment_id):
        """Check if a comment still exists on Facebook"""
        if not self.facebook_apps:
            return True  # Assume exists if can't check
            
        facebook_app = self.facebook_apps[0]
        access_token = facebook_app.get('access_token')
        
        if not access_token:
            return True  # Assume exists if can't check
            
        try:
            url = f"https://graph.facebook.com/v18.0/{comment_id}"
            params = {'access_token': access_token, 'fields': 'id'}
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return True
            else:
                result = response.json()
                if self.is_comment_not_found_error(result):
                    return False
                return True  # Assume exists for other errors
                
        except Exception as e:
            print(f"⚠️ Error checking comment {comment_id}: {e}")
            return True  # Assume exists if error

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
