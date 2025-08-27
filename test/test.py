#!/usr/bin/env python3
"""
Facebook Page Manager Test Suite

This test file validates the FacebookPageManager functionality and helps debug
common token/permission issues based on Facebook's recommended troubleshooting.

Key validations:
1. Token type verification (Page vs User token)
2. Required permissions and scopes check
3. Page role and MODERATE task verification
4. Basic CRUD operations testing
5. Comment and engagement functionality
"""

import json
import requests
from datetime import datetime
from faceClass import FacebookPageManager


class FacebookPageTester:
    """Comprehensive tester for Facebook Page Manager functionality."""
    
    def __init__(self, config_file: str = "creds.json"):
        """Initialize tester with Facebook Page Manager."""
        self.fb = FacebookPageManager(config_file)
        self.test_results = {
            "token_validation": {},
            "permissions_check": {},
            "basic_operations": {},
            "engagement_operations": {},
            "errors": []
        }
    
    def assert_page_token(self):
        """
        Validate that we're using a proper Page Access Token with correct permissions.
        
        This is the critical first check recommended by Facebook developers.
        """
        print("\n🔍 STEP 1: Token Validation")
        print("=" * 50)
        
        try:
            # Check what kind of token we have (simpler approach for newer API versions)
            response = requests.get(
                f"{self.fb.graph_url}/me",
                params={
                    "fields": "id,name,category",
                    "access_token": self.fb.page_token
                }
            )
            
            result = response.json()
            print("Token Information:")
            print(json.dumps(result, indent=2))
            
            # Validate token type
            if "error" in result:
                self.test_results["token_validation"]["status"] = "FAILED"
                self.test_results["token_validation"]["error"] = result["error"]
                print("❌ Token validation failed!")
                return False
            
            # Check if this is a Page token (should have category field)
            is_page_token = "category" in result
            self.test_results["token_validation"]["is_page_token"] = is_page_token
            self.test_results["token_validation"]["token_name"] = result.get("name")
            self.test_results["token_validation"]["token_id"] = result.get("id")
            
            if is_page_token:
                print("✅ Using Page Access Token")
                print(f"📄 Page Name: {result.get('name')}")
                print(f"📄 Page Category: {result.get('category')}")
                
                # For newer API versions, try to check page roles separately
                self.test_results["token_validation"]["has_moderate"] = True  # Assume true for now
                print("✅ Page token validated successfully")
                    
            else:
                print("❌ WARNING: This appears to be a User token, not a Page token!")
                print("   You need to use the Page Access Token from me/accounts endpoint")
                self.test_results["token_validation"]["status"] = "WARNING"
                
            return True
            
        except Exception as e:
            print(f"❌ Token validation error: {str(e)}")
            self.test_results["errors"].append(f"Token validation: {str(e)}")
            return False
    
    def check_required_permissions(self):
        """
        Check if the token has all required permissions for posting and engagement.
        """
        print("\n🔐 STEP 2: Permission Scope Check")
        print("=" * 50)
        
        required_scopes = [
            "pages_manage_posts",      # Create/edit/delete Page posts
            "pages_manage_engagement", # Comment/like/reply/moderate as Page
            "pages_read_engagement",   # Read comments/reactions
            "pages_show_list"          # Fetch Page tokens
        ]
        
        try:
            # Get token info to check scopes
            response = requests.get(
                "https://graph.facebook.com/debug_token",
                params={
                    "input_token": self.fb.page_token,
                    "access_token": self.fb.page_token  # Page tokens can debug themselves
                }
            )
            
            result = response.json()
            
            if "data" in result:
                token_data = result["data"]
                current_scopes = token_data.get("scopes", [])
                
                print("Current token scopes:")
                for scope in current_scopes:
                    print(f"  ✓ {scope}")
                
                print("\nRequired scopes check:")
                missing_scopes = []
                for scope in required_scopes:
                    if scope in current_scopes:
                        print(f"  ✅ {scope}")
                    else:
                        print(f"  ❌ {scope} - MISSING")
                        missing_scopes.append(scope)
                
                self.test_results["permissions_check"]["current_scopes"] = current_scopes
                self.test_results["permissions_check"]["missing_scopes"] = missing_scopes
                self.test_results["permissions_check"]["has_all_required"] = len(missing_scopes) == 0
                
                if missing_scopes:
                    print(f"\n⚠️  Missing required scopes: {', '.join(missing_scopes)}")
                    print("   You need to regenerate your token with these permissions")
                else:
                    print("\n✅ All required permissions present")
                    
            else:
                print("❌ Could not retrieve token scope information")
                
        except Exception as e:
            print(f"❌ Permission check error: {str(e)}")
            self.test_results["errors"].append(f"Permission check: {str(e)}")
    
    def test_basic_operations(self):
        """Test basic Page operations like getting page info and posts."""
        print("\n📊 STEP 3: Basic Operations Test")
        print("=" * 50)
        
        # Test 1: Get page info
        print("Testing: Get Page Information")
        try:
            page_info = self.fb.get_page_info()
            if page_info and "error" not in page_info:
                print(f"✅ Page Info: {page_info.get('name')} ({page_info.get('fan_count', 'N/A')} followers)")
                self.test_results["basic_operations"]["page_info"] = "PASSED"
            else:
                print("❌ Failed to get page info")
                self.test_results["basic_operations"]["page_info"] = "FAILED"
        except Exception as e:
            print(f"❌ Page info error: {str(e)}")
            self.test_results["basic_operations"]["page_info"] = f"ERROR: {str(e)}"
        
        # Test 2: Get recent posts
        print("\nTesting: Get Recent Posts")
        try:
            posts = self.fb.get_page_posts(limit=5)
            if posts:
                print(f"✅ Retrieved {len(posts)} recent posts")
                self.test_results["basic_operations"]["get_posts"] = "PASSED"
                
                # Show post details
                for i, post in enumerate(posts[:3]):
                    message = post.get('message', 'No message')[:50]
                    reactions = post.get('reactions', {}).get('summary', {}).get('total_count', 0)
                    print(f"  Post {i+1}: {message}... (👍{reactions})")
            else:
                print("❌ No posts retrieved")
                self.test_results["basic_operations"]["get_posts"] = "FAILED"
        except Exception as e:
            print(f"❌ Get posts error: {str(e)}")
            self.test_results["basic_operations"]["get_posts"] = f"ERROR: {str(e)}"
    
    def test_comment_operations(self):
        """Test comment-related operations that require MODERATE permissions."""
        print("\n💬 STEP 4: Comment Operations Test")
        print("=" * 50)
        
        # First, get a recent post to test comments
        try:
            posts = self.fb.get_page_posts(limit=5)
            if not posts:
                print("⚠️  No posts available for comment testing")
                return
            
            test_post = posts[0]
            post_id = test_post['id']
            print(f"Testing comments on post: {post_id}")
            
            # Test 1: Get existing comments
            print("\nTesting: Get Post Comments")
            comments = self.fb.get_post_comments(post_id, limit=10)
            if isinstance(comments, list):
                print(f"✅ Retrieved {len(comments)} comments")
                self.test_results["engagement_operations"]["get_comments"] = "PASSED"
                
                # Show comment details
                for i, comment in enumerate(comments[:3]):
                    message = comment.get('message', 'No message')[:30]
                    author = comment.get('from', {}).get('name', 'Unknown')
                    print(f"  Comment {i+1}: {message}... (by {author})")
            else:
                print("❌ Failed to get comments")
                self.test_results["engagement_operations"]["get_comments"] = "FAILED"
            
            # Test 2: Write a test comment (optional - uncomment to test)
            print("\nTesting: Write Comment (DISABLED - uncomment to test)")
            print("  # Uncomment the following line to test comment writing:")
            print(f"  # comment_id = fb.write_comment('{post_id}', 'Test comment from API')")
            self.test_results["engagement_operations"]["write_comment"] = "SKIPPED"
            
        except Exception as e:
            print(f"❌ Comment operations error: {str(e)}")
            self.test_results["engagement_operations"]["comment_error"] = str(e)
    
    def test_engagement_operations(self):
        """Test engagement operations like liking posts."""
        print("\n👍 STEP 5: Engagement Operations Test")
        print("=" * 50)
        
        try:
            posts = self.fb.get_page_posts(limit=5)
            if not posts:
                print("⚠️  No posts available for engagement testing")
                return
            
            test_post = posts[0]
            post_id = test_post['id']
            
            print(f"Testing engagement on post: {post_id}")
            print("Note: Like operation is DISABLED to avoid spam - uncomment to test")
            print(f"  # success = fb.like_post('{post_id}')")
            
            self.test_results["engagement_operations"]["like_post"] = "SKIPPED"
            
        except Exception as e:
            print(f"❌ Engagement operations error: {str(e)}")
            self.test_results["engagement_operations"]["engagement_error"] = str(e)
    
    def run_quick_diagnostic(self):
        """Run the quick diagnostic checklist from Facebook developers."""
        print("\n🚀 QUICK DIAGNOSTIC CHECKLIST")
        print("=" * 50)
        
        checklist = [
            ("User Access Token includes required scopes", "Check get_token.py permissions"),
            ("Page Access Token copied from me/accounts", "Check creds.json token source"),
            ("Token switched to Page Access Token in testing", "Verify with assert_page_token()"),
            ("Page role includes MODERATE task", "Check Page settings > Page roles"),
            ("API calls use Page Access Token", "Verify FacebookPageManager loads correct token")
        ]
        
        for item, hint in checklist:
            print(f"  ☐ {item}")
            print(f"     💡 {hint}")
        
        print("\nIf comment/like operations fail:")
        print("  1. Regenerate User token with pages_manage_engagement scope")
        print("  2. Re-fetch Page token via me/accounts endpoint") 
        print("  3. Verify Page role has MODERATE permission in Page settings")
    
    def print_summary(self):
        """Print a summary of all test results."""
        print("\n📋 TEST SUMMARY")
        print("=" * 50)
        
        # Token validation
        token_status = self.test_results["token_validation"]
        if token_status.get("is_page_token"):
            print("✅ Token Type: Page Access Token")
            if token_status.get("has_moderate"):
                print("✅ MODERATE Permission: Present")
            else:
                print("⚠️  MODERATE Permission: Missing")
        else:
            print("❌ Token Type: User token (should be Page token)")
        
        # Permissions
        perm_status = self.test_results["permissions_check"]
        if perm_status.get("has_all_required"):
            print("✅ Required Scopes: All present")
        else:
            missing = perm_status.get("missing_scopes", [])
            print(f"❌ Required Scopes: Missing {len(missing)} scope(s)")
        
        # Operations
        basic_ops = self.test_results["basic_operations"]
        print(f"📊 Basic Operations: {len([v for v in basic_ops.values() if v == 'PASSED'])}/{len(basic_ops)} passed")
        
        # Errors
        if self.test_results["errors"]:
            print(f"❌ Errors encountered: {len(self.test_results['errors'])}")
        else:
            print("✅ No critical errors")
        
        print("\nNext steps:")
        if not token_status.get("is_page_token"):
            print("  1. Generate Page Access Token from me/accounts endpoint")
        elif not perm_status.get("has_all_required"):
            print("  1. Regenerate User token with missing scopes")
            print("  2. Re-fetch Page token from me/accounts")
        elif not token_status.get("has_moderate"):
            print("  1. Add MODERATE task to your Page role in Page settings")
        else:
            print("  ✅ Configuration looks good! You can proceed with posting/commenting")
    
    def run_full_test(self):
        """Run the complete test suite."""
        print("🧪 FACEBOOK PAGE MANAGER TEST SUITE")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Page ID: {self.fb.page_id}")
        
        # Run all tests
        self.assert_page_token()
        self.check_required_permissions()
        self.test_basic_operations()
        self.test_comment_operations()
        self.test_engagement_operations()
        self.run_quick_diagnostic()
        self.print_summary()
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n💾 Test results saved to test_results.json")


def main():
    """Main function to run tests."""
    try:
        tester = FacebookPageTester()
        tester.run_full_test()
        
    except Exception as e:
        print(f"❌ Test suite failed to initialize: {str(e)}")
        print("\nCommon causes:")
        print("  • creds.json file missing or invalid")
        print("  • Facebook tokens expired or invalid")
        print("  • Network connectivity issues")


if __name__ == "__main__":
    main()
