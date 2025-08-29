#!/usr/bin/env python3
"""
Comment Sentiment Analysis Agent
================================

This module analyzes comments using OpenAI API to determine sentiment
(positive, neutral, negative) and stores the results in the database.
"""

import sys
import os
import json
from datetime import datetime
from openai import OpenAI

# Add parent directory to path to import routes
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes.comment import get_unqlite_db, get_comments_from_db, get_posts_from_db

class CommentSentimentAnalyzer:
    def __init__(self):
        """Initialize the sentiment analyzer with OpenAI client"""
        self.client = None
        self.load_openai_config()
    
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
    
    def analyze_sentiment(self, comment_text):
        """
        Analyze sentiment of a comment using OpenAI API
        
        Args:
            comment_text (str): The comment text to analyze
            
        Returns:
            dict: Contains sentiment label and confidence
        """
        if not self.client:
            return {"sentiment": "neutral", "confidence": 0.0, "error": "OpenAI client not initialized"}
        
        if not comment_text or not comment_text.strip():
            return {"sentiment": "neutral", "confidence": 0.0, "error": "Empty comment"}
        
        try:
            prompt = f"""
            Analyze the sentiment of the following comment and classify it as exactly one of these three labels:
            - positive: for positive, happy, supportive, appreciative, or enthusiastic comments
            - negative: for negative, angry, critical, disappointed, or hostile comments  
            - neutral: for neutral, informational, questions, or mixed sentiment comments

            Comment: "{comment_text}"

            Respond with only the sentiment label (positive, negative, or neutral) and nothing else.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert. Classify comments as positive, negative, or neutral."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            sentiment = response.choices[0].message.content.strip().lower()
            
            # Validate the response
            if sentiment in ["positive", "negative", "neutral"]:
                return {
                    "sentiment": sentiment,
                    "confidence": 1.0,
                    "analyzed_at": datetime.now().isoformat()
                }
            else:
                # Fallback to neutral if unexpected response
                print(f"⚠️ Unexpected sentiment response: {sentiment}, defaulting to neutral")
                return {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "analyzed_at": datetime.now().isoformat(),
                    "note": f"Unexpected response: {sentiment}"
                }
                
        except Exception as e:
            print(f"❌ Error analyzing sentiment: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "error": str(e),
                "analyzed_at": datetime.now().isoformat()
            }
    
    def get_all_comments_from_db(self):
        """
        Retrieve all comments from the database
        
        Returns:
            list: List of all comments with their metadata
        """
        db = get_unqlite_db()
        all_comments = []
        
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
                    
                    # Only process comment keys
                    if key_str.startswith('comments:'):
                        # Decode value
                        if hasattr(value_bytes, 'decode'):
                            value_str = value_bytes.decode('utf-8')
                        else:
                            value_str = str(value_bytes)
                        
                        comments_data = json.loads(value_str)
                        comments_list = comments_data.get('comments', [])
                        
                        for comment in comments_list:
                            all_comments.append({
                                'key': key_str,
                                'post_id': comments_data.get('post_id'),
                                'content_id': comments_data.get('content_id'),
                                'comment_id': comment.get('id'),
                                'message': comment.get('message', ''),
                                'author_name': comment.get('from', {}).get('name', 'Unknown'),
                                'created_time': comment.get('created_time'),
                                'like_count': comment.get('like_count', 0),
                                'original_data': comment
                            })
                            
                except Exception as e:
                    print(f"Error processing comment key {raw_key}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error retrieving comments: {e}")
        finally:
            db.close()
        
        return all_comments
    
    def store_sentiment_in_db(self, comment_key, comment_id, sentiment_data):
        """
        Store sentiment analysis results in the database
        
        Args:
            comment_key (str): The database key for the comment
            comment_id (str): The Facebook comment ID
            sentiment_data (dict): The sentiment analysis results
        """
        db = get_unqlite_db()
        
        try:
            # Create a sentiment key
            sentiment_key = f"sentiment:{comment_key}:{comment_id}"
            
            # Store sentiment data
            db[sentiment_key] = json.dumps(sentiment_data)
            db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error storing sentiment: {e}")
            return False
        finally:
            db.close()
    
    def get_sentiment_from_db(self, comment_key, comment_id):
        """
        Retrieve sentiment analysis from database if it exists
        
        Args:
            comment_key (str): The database key for the comment
            comment_id (str): The Facebook comment ID
            
        Returns:
            dict: Sentiment data if found, None otherwise
        """
        db = get_unqlite_db()
        
        try:
            sentiment_key = f"sentiment:{comment_key}:{comment_id}"
            
            if sentiment_key.encode('utf-8') in db:
                value_bytes = db[sentiment_key.encode('utf-8')]
                value_str = value_bytes.decode('utf-8') if hasattr(value_bytes, 'decode') else str(value_bytes)
                return json.loads(value_str)
            elif sentiment_key in db:
                value_bytes = db[sentiment_key]
                value_str = value_bytes.decode('utf-8') if hasattr(value_bytes, 'decode') else str(value_bytes)
                return json.loads(value_str)
                
        except Exception as e:
            print(f"Error retrieving sentiment: {e}")
        finally:
            db.close()
            
        return None
    
    def analyze_all_comments(self, force_reanalyze=False):
        """
        Analyze sentiment for all comments in the database
        
        Args:
            force_reanalyze (bool): Whether to re-analyze already processed comments
            
        Returns:
            dict: Summary of analysis results
        """
        print("🤖 Starting comment sentiment analysis...")
        print("=" * 50)
        
        comments = self.get_all_comments_from_db()
        
        if not comments:
            print("❌ No comments found in database")
            return {"total": 0, "analyzed": 0, "skipped": 0, "errors": 0}
        
        print(f"📊 Found {len(comments)} comments to analyze")
        
        stats = {
            "total": len(comments),
            "analyzed": 0,
            "skipped": 0,
            "errors": 0,
            "sentiments": {"positive": 0, "negative": 0, "neutral": 0}
        }
        
        for i, comment in enumerate(comments, 1):
            comment_key = comment['key']
            comment_id = comment['comment_id']
            message = comment['message']
            
            print(f"\n[{i}/{len(comments)}] Processing comment {comment_id}")
            
            # Check if already analyzed (unless force_reanalyze is True)
            existing_sentiment = self.get_sentiment_from_db(comment_key, comment_id)
            if existing_sentiment and not force_reanalyze:
                print(f"⏭️ Skipping - already analyzed as '{existing_sentiment.get('sentiment', 'unknown')}'")
                stats["skipped"] += 1
                stats["sentiments"][existing_sentiment.get("sentiment", "neutral")] += 1
                continue
            
            # Analyze sentiment
            print(f"💭 Analyzing: \"{message[:50]}{'...' if len(message) > 50 else ''}\"")
            
            sentiment_result = self.analyze_sentiment(message)
            
            if "error" in sentiment_result:
                print(f"❌ Error: {sentiment_result['error']}")
                stats["errors"] += 1
                continue
            
            # Store result
            sentiment_storage = {
                "comment_id": comment_id,
                "comment_key": comment_key,
                "message": message,
                "author_name": comment['author_name'],
                "created_time": comment['created_time'],
                **sentiment_result
            }
            
            if self.store_sentiment_in_db(comment_key, comment_id, sentiment_storage):
                sentiment_label = sentiment_result['sentiment']
                print(f"✅ Analyzed as '{sentiment_label}' and stored successfully")
                stats["analyzed"] += 1
                stats["sentiments"][sentiment_label] += 1
            else:
                print(f"❌ Failed to store sentiment result")
                stats["errors"] += 1
        
        print("\n" + "=" * 50)
        print("📈 ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"Total comments: {stats['total']}")
        print(f"Newly analyzed: {stats['analyzed']}")
        print(f"Already processed: {stats['skipped']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nSentiment distribution:")
        print(f"  Positive: {stats['sentiments']['positive']}")
        print(f"  Negative: {stats['sentiments']['negative']}")
        print(f"  Neutral: {stats['sentiments']['neutral']}")
        
        return stats

def main():
    """Main function to run sentiment analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze sentiment of Facebook comments")
    parser.add_argument("--force", action="store_true", help="Re-analyze already processed comments")
    parser.add_argument("--test", action="store_true", help="Test with a sample comment")
    
    args = parser.parse_args()
    
    analyzer = CommentSentimentAnalyzer()
    
    if args.test:
        # Test with sample comments
        test_comments = [
            "This is amazing! I love it so much! 🔥🔥🔥",
            "This is terrible. I hate this completely.",
            "Can you provide more information about this?"
        ]
        
        print("🧪 Testing sentiment analysis with sample comments:")
        for comment in test_comments:
            result = analyzer.analyze_sentiment(comment)
            print(f"Comment: \"{comment}\"")
            print(f"Sentiment: {result.get('sentiment', 'unknown')}")
            print("-" * 40)
    else:
        # Analyze all comments
        analyzer.analyze_all_comments(force_reanalyze=args.force)

if __name__ == "__main__":
    main()
