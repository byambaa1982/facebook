import requests
import webbrowser
import json
from urllib.parse import urlencode, parse_qs, urlparse

# You need to get these from your Facebook App settings
APP_ID = "867379254182990"  # Replace with your App ID
APP_SECRET = "34ce324b0c397825fb6fa1f08fc99089"  # Replace with your App Secret
REDIRECT_URI = "https://localhost/"  # This can be any URL you control

# Required permissions for posting to pages and managing engagement
PERMISSIONS = [
    "pages_manage_posts",        # Create/edit/delete Page posts
    "pages_manage_engagement",   # Comment/like/reply/moderate as Page  
    "pages_read_engagement",     # Read comments/reactions
    "pages_show_list"           # Fetch Page tokens
]

def get_user_access_token():
    """Step 1: Get user access token via OAuth"""
    
    # Build authorization URL
    auth_params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": ",".join(PERMISSIONS),
        "response_type": "code"
    }
    
    auth_url = f"https://www.facebook.com/v21.0/dialog/oauth?{urlencode(auth_params)}"
    
    print("1. Opening Facebook authorization page...")
    print(f"URL: {auth_url}")
    webbrowser.open(auth_url)
    
    print("\n2. After authorizing, copy the 'code' parameter from the redirect URL")
    code = input("Enter the authorization code: ").strip()
    
    # Exchange code for access token
    token_params = {
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    
    token_url = "https://graph.facebook.com/v21.0/oauth/access_token"
    response = requests.get(token_url, params=token_params)
    
    if response.status_code != 200:
        print("Error getting access token:", response.text)
        return None
        
    token_data = response.json()
    return token_data["access_token"]

def get_page_access_token(user_token):
    """Step 2: Get long-lived page access token"""
    
    # Get user's pages
    pages_url = f"https://graph.facebook.com/v21.0/me/accounts"
    response = requests.get(pages_url, params={"access_token": user_token})
    
    if response.status_code != 200:
        print("Error getting pages:", response.text)
        return None
        
    pages_data = response.json()
    
    print("\n3. Your pages:")
    for i, page in enumerate(pages_data["data"]):
        print(f"   {i+1}. {page['name']} (ID: {page['id']})")
    
    # Select page
    while True:
        try:
            choice = int(input("\nSelect page number: ")) - 1
            if 0 <= choice < len(pages_data["data"]):
                selected_page = pages_data["data"][choice]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    page_token = selected_page["access_token"]
    page_id = selected_page["id"]
    page_name = selected_page["name"]
    
    print(f"\n4. Success! Page access token generated for '{page_name}'")
    print(f"   Page ID: {page_id}")
    print(f"   Page Token: {page_token}")
    
    return page_token, page_id

def save_config(page_id, page_token):
    """Save page configuration to config.json"""
    config = {
        "page_id": page_id,
        "page_token": page_token
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration saved to config.json")

def verify_page_token(page_token):
    """Verify the page token works and show token info"""
    print("\n6. Verifying Page Access Token...")
    
    # Test the token
    response = requests.get(
        "https://graph.facebook.com/v21.0/me",
        params={
            "fields": "id,name,category,fan_count",
            "access_token": page_token
        }
    )
    
    if response.status_code == 200:
        page_info = response.json()
        print("✅ Page token verification successful!")
        print(f"   Page: {page_info.get('name')}")
        print(f"   Category: {page_info.get('category')}")
        print(f"   Followers: {page_info.get('fan_count', 'N/A')}")
        return True
    else:
        print("❌ Page token verification failed!")
        print(f"   Error: {response.text}")
        return False

def main():
    print("Facebook Page Access Token Generator")
    print("="*50)
    
    if APP_ID == "YOUR_APP_ID" or APP_SECRET == "YOUR_APP_SECRET":
        print("Error: Please update APP_ID and APP_SECRET in this script first!")
        print("Get these from: https://developers.facebook.com/apps/")
        return
    
    # Step 1: Get user access token
    user_token = get_user_access_token()
    if not user_token:
        return
        
    print(f"User access token: {user_token}")
    
    # Step 2: Get page access token
    result = get_page_access_token(user_token)
    if not result:
        return
        
    page_token, page_id = result
    
    # Step 3: Verify the page token
    if not verify_page_token(page_token):
        return
    
    # Step 4: Save configuration
    save_config(page_id, page_token)
    
    print(f"\n7. Setup complete! You can now run:")
    print(f"   python test.py  # Test the configuration")
    print(f"   python demo.py  # Run demos")
    print(f"\n💡 The page token is now saved in config.json and ready to use!")

if __name__ == "__main__":
    main()
