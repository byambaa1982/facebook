import os
import requests
import json
from typing import List, Dict, Optional, Union
from datetime import datetime

class FacebookPageManager:
    """
    A comprehensive Facebook Page management class for posting content,
    managing comments, and reviewing page activity.
    """
    
    def __init__(self, config_file: str = "creds.json"):
        """
        Initialize the Facebook Page Manager.
        
        Args:
            config_file: Path to JSON config file containing page_id and page_token
        """
        self.graph_url = "https://graph.facebook.com/v21.0"
        self.page_id = None
        self.page_token = None
        self._load_config(config_file)
    
    def _load_config(self, config_file: str):
        """Load configuration from file or environment variables."""
        try:
            with open(config_file, "r", encoding='utf-8') as f:
                config = json.load(f)
            self.page_id = config["page_id"]
            self.page_token = config["page_token"]
        except FileNotFoundError:
            # Fallback to environment variables
            self.page_id = os.getenv("FB_PAGE_ID")
            self.page_token = os.getenv("FB_PAGE_TOKEN")
            
        if not self.page_id or not self.page_token:
            raise ValueError("Missing Facebook Page ID or Token. Check creds.json or environment variables.")
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError:
            # Pretty-print Graph API error
            try:
                error_data = response.json()
                print("Facebook API Error:", error_data)
                return {"error": error_data}
            except Exception:
                print("HTTP Error (raw):", response.text)
                raise
    
    # ==================== POSTING METHODS ====================
    
    def post_text(self, message: str, link: str = None) -> str:
        """
        Create a text post on the Page.
        
        Args:
            message: The text content of the post
            link: Optional URL to include in the post
            
        Returns:
            Post ID if successful
        """
        url = f"{self.graph_url}/{self.page_id}/feed"
        data = {
            "message": message,
            "access_token": self.page_token
        }
        
        if link:
            data["link"] = link
            
        response = requests.post(url, data=data)
        result = self._handle_response(response)
        
        if "error" not in result:
            post_id = result.get("id")
            print(f"✅ Text post created: {post_id}")
            return post_id
        return None
    
    def post_photo(self, image_path: str, caption: str = "") -> str:
        """
        Post a photo from local file.
        
        Args:
            image_path: Path to the image file
            caption: Optional caption for the photo
            
        Returns:
            Photo post ID if successful
        """
        url = f"{self.graph_url}/{self.page_id}/photos"
        
        try:
            with open(image_path, "rb") as img_file:
                response = requests.post(
                    url,
                    data={
                        "caption": caption,
                        "access_token": self.page_token
                    },
                    files={"source": img_file}
                )
        except FileNotFoundError:
            print(f"❌ Image file not found: {image_path}")
            return None
            
        result = self._handle_response(response)
        
        if "error" not in result:
            photo_id = result.get("post_id") or result.get("id")
            print(f"📸 Photo posted: {photo_id}")
            return photo_id
        return None
    
    def post_photo_url(self, image_url: str, caption: str = "") -> str:
        """
        Post a photo from URL.
        
        Args:
            image_url: Public URL of the image
            caption: Optional caption for the photo
            
        Returns:
            Photo post ID if successful
        """
        url = f"{self.graph_url}/{self.page_id}/photos"
        data = {
            "url": image_url,
            "caption": caption,
            "access_token": self.page_token
        }
        
        response = requests.post(url, data=data)
        result = self._handle_response(response)
        
        if "error" not in result:
            photo_id = result.get("post_id") or result.get("id")
            print(f"📸 Photo posted from URL: {photo_id}")
            return photo_id
        return None
    
    # ==================== COMMENT METHODS ====================
    
    def write_comment(self, post_id: str, message: str) -> str:
        """
        Write a comment on a post.
        
        Args:
            post_id: ID of the post to comment on
            message: Comment text
            
        Returns:
            Comment ID if successful
        """
        url = f"{self.graph_url}/{post_id}/comments"
        data = {
            "message": message,
            "access_token": self.page_token
        }
        
        response = requests.post(url, data=data)
        result = self._handle_response(response)
        
        if "error" not in result:
            comment_id = result.get("id")
            print(f"💬 Comment added: {comment_id}")
            return comment_id
        return None
    
    def get_post_comments(self, post_id: str, limit: int = 25) -> List[Dict]:

        url = f"{self.graph_url}/{post_id}/comments"
        params = {
            "fields": "id,message,created_time,from,like_count,comment_count",
            "limit": limit,
            "access_token": self.page_token
        }
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        
        if "error" not in result:
            return result.get("data", [])
        return []
    
    def reply_to_comment(self, comment_id: str, message: str) -> str:

        url = f"{self.graph_url}/{comment_id}/comments"
        data = {
            "message": message,
            "access_token": self.page_token
        }
        
        response = requests.post(url, data=data)
        result = self._handle_response(response)
        
        if "error" not in result:
            reply_id = result.get("id")
            print(f"↩️ Reply added: {reply_id}")
            return reply_id
        return None
    
    def delete_comment(self, comment_id: str) -> bool:

        url = f"{self.graph_url}/{comment_id}"
        response = requests.delete(url, params={"access_token": self.page_token})
        result = self._handle_response(response)
        
        success = result is True or result.get("success") is True
        if success:
            print(f"🗑️ Comment deleted: {comment_id}")
        return success
    
    # ==================== REVIEW METHODS ====================
    
    def get_page_posts(self, limit: int = 25) -> List[Dict]:
        """
        Get recent posts from the page.

        """
        url = f"{self.graph_url}/{self.page_id}/posts"
        params = {
            "fields": "id,message,created_time,permalink_url,status_type,reactions.summary(true),comments.summary(true),shares",
            "limit": limit,
            "access_token": self.page_token
        }
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        
        if "error" not in result:
            return result.get("data", [])
        return []
    
    def get_post_insights(self, post_id: str) -> Dict:
        """
        Get insights/analytics for a specific post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            Post insights data
        """
        url = f"{self.graph_url}/{post_id}/insights"
        params = {
            "metric": "post_impressions,post_reach,post_reactions_by_type_total",
            "access_token": self.page_token
        }
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        
        if "error" not in result:
            return result.get("data", [])
        return []
    
    def review_recent_activity(self, days: int = 7) -> Dict:
        """
        Get a summary of recent page activity.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Activity summary
        """
        posts = self.get_page_posts(limit=50)
        
        # Filter posts from last N days
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_posts = []
        
        for post in posts:
            created_time = datetime.strptime(post['created_time'], '%Y-%m-%dT%H:%M:%S%z').timestamp()
            if created_time >= cutoff_date:
                recent_posts.append(post)
        
        # Calculate summary statistics
        total_reactions = sum(post.get('reactions', {}).get('summary', {}).get('total_count', 0) for post in recent_posts)
        total_comments = sum(post.get('comments', {}).get('summary', {}).get('total_count', 0) for post in recent_posts)
        total_shares = sum(post.get('shares', {}).get('count', 0) for post in recent_posts)
        
        summary = {
            "period_days": days,
            "total_posts": len(recent_posts),
            "total_reactions": total_reactions,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "average_engagement": (total_reactions + total_comments + total_shares) / max(len(recent_posts), 1),
            "posts": recent_posts
        }
        
        return summary
    
    # ==================== UTILITY METHODS ====================
    
    def like_post(self, post_id: str) -> bool:
        """
        Like a post as the page.
        
        Args:
            post_id: ID of the post to like
            
        Returns:
            True if successful
        """
        url = f"{self.graph_url}/{post_id}/likes"
        data = {"access_token": self.page_token}
        
        response = requests.post(url, data=data)
        result = self._handle_response(response)
        
        success = result is True or result.get("success") is True
        if success:
            print(f"👍 Liked post: {post_id}")
        return success
    
    def delete_post(self, post_id: str) -> bool:
        """
        Delete a post.
        
        Args:
            post_id: ID of the post to delete
            
        Returns:
            True if successful
        """
        url = f"{self.graph_url}/{post_id}"
        response = requests.delete(url, params={"access_token": self.page_token})
        result = self._handle_response(response)
        
        success = result is True or result.get("success") is True
        if success:
            print(f"🗑️ Post deleted: {post_id}")
        return success
    
    def get_page_info(self) -> Dict:
        """
        Get basic information about the page.
        
        Returns:
            Page information
        """
        url = f"{self.graph_url}/{self.page_id}"
        params = {
            "fields": "id,name,about,category,fan_count,followers_count,website,phone",
            "access_token": self.page_token
        }
        
        response = requests.get(url, params=params)
        result = self._handle_response(response)
        
        if "error" not in result:
            return result
        return {}
    
    def print_activity_summary(self, days: int = 7):
        """
        Print a formatted summary of recent page activity.
        
        Args:
            days: Number of days to review
        """
        print(f"\n📊 Page Activity Summary (Last {days} days)")
        print("=" * 50)
        
        activity = self.review_recent_activity(days)
        
        print(f"📝 Total Posts: {activity['total_posts']}")
        print(f"❤️ Total Reactions: {activity['total_reactions']}")
        print(f"💬 Total Comments: {activity['total_comments']}")
        print(f"🔄 Total Shares: {activity['total_shares']}")
        print(f"📈 Average Engagement per Post: {activity['average_engagement']:.1f}")
        
        if activity['posts']:
            print(f"\n📋 Recent Posts:")
            for post in activity['posts'][:5]:  # Show top 5
                reactions = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
                comments = post.get('comments', {}).get('summary', {}).get('total_count', 0)
                message = post.get('message', 'No message')[:50] + "..." if len(post.get('message', '')) > 50 else post.get('message', 'No message')
                print(f"  • {message} | 👍{reactions} 💬{comments}")


# Example usage and demo functions
if __name__ == "__main__":
    # Initialize the Facebook Page Manager
    fb = FacebookPageManager()
    
    # Demo: Get page info
    print("🏢 Page Information:")
    page_info = fb.get_page_info()
    if page_info:
        print(f"Name: {page_info.get('name')}")
        print(f"Followers: {page_info.get('followers_count', 'N/A')}")
    
    # Demo: Review recent activity
    fb.print_activity_summary(days=7)
    
    # Uncomment to test posting:
    # post_id = fb.post_text("Hello from FacebookPageManager class! 🚀")
    # fb.write_comment(post_id, "This is an automated comment!")
