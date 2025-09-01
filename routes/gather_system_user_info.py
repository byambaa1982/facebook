#!/usr/bin/env python3
"""
Script to gather comprehensive system user information for updating system_user.json
"""

import os
import json
import requests
from datetime import datetime

def load_system_user_token():
    """Load system user token from JSON file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    system_user_file = os.path.join(script_dir, 'system_user.json')
    
    with open(system_user_file, 'r') as f:
        data = json.load(f)
    
    # Handle typo in original file
    token_key = 'system_user_access_toke' if 'system_user_access_toke' in data else 'system_user_access_token'
    return data[token_key]

def get_comprehensive_system_user_info():
    """Get comprehensive information about system user and owned accounts"""
    facebook_graph_url = "https://graph.facebook.com/v19.0"
    token = load_system_user_token()
    
    system_info = {
        "system_user_access_token": token,
        "last_updated": datetime.now().isoformat(),
        "app_info": {},
        "permissions": [],
        "facebook_pages": [],
        "instagram_accounts": []
    }
    
    try:
        # Get app information
        print("Getting app information...")
        app_response = requests.get(
            f"{facebook_graph_url}/me",
            params={'access_token': token},
            timeout=30
        )
        
        if app_response.status_code == 200:
            app_data = app_response.json()
            system_info["app_info"] = {
                "id": app_data.get("id"),
                "name": app_data.get("name"),
                "app_type": app_data.get("app_type", "system_user")
            }
            print(f"  ✓ App: {app_data.get('name')} (ID: {app_data.get('id')})")
        
        # Get permissions
        print("Getting permissions...")
        perm_response = requests.get(
            f"{facebook_graph_url}/me/permissions",
            params={'access_token': token},
            timeout=30
        )
        
        if perm_response.status_code == 200:
            permissions_data = perm_response.json().get('data', [])
            system_info["permissions"] = [
                {
                    "permission": perm.get("permission"),
                    "status": perm.get("status")
                }
                for perm in permissions_data
            ]
            granted_count = len([p for p in permissions_data if p.get("status") == "granted"])
            print(f"  ✓ Permissions: {granted_count} granted out of {len(permissions_data)} total")
        
        # Get Facebook pages
        print("Getting Facebook pages...")
        pages_response = requests.get(
            f"{facebook_graph_url}/me/accounts",
            params={
                'access_token': token,
                'fields': 'id,name,category,access_token,instagram_business_account,fan_count,about,website,phone'
            },
            timeout=30
        )
        
        if pages_response.status_code == 200:
            pages_data = pages_response.json().get('data', [])
            
            for page in pages_data:
                page_info = {
                    "id": page.get("id"),
                    "name": page.get("name"),
                    "category": page.get("category"),
                    "fan_count": page.get("fan_count", 0),
                    "about": page.get("about"),
                    "website": page.get("website"),
                    "phone": page.get("phone"),
                    "access_token": page.get("access_token"),
                    "has_instagram_account": "instagram_business_account" in page
                }
                
                system_info["facebook_pages"].append(page_info)
                print(f"  ✓ Page: {page.get('name')} (ID: {page.get('id')}) - Fans: {page.get('fan_count', 0)}")
                
                # Get detailed Instagram account info if connected
                if page.get("access_token"):
                    page_token = page.get("access_token")
                    page_id = page.get("id")
                    
                    ig_response = requests.get(
                        f"{facebook_graph_url}/{page_id}",
                        params={
                            'access_token': page_token,
                            'fields': 'instagram_business_account{id,username,name,biography,website,profile_picture_url,followers_count,follows_count,media_count}'
                        },
                        timeout=30
                    )
                    
                    if ig_response.status_code == 200:
                        ig_data = ig_response.json()
                        instagram_account = ig_data.get('instagram_business_account')
                        
                        if instagram_account:
                            instagram_info = {
                                "id": instagram_account.get("id"),
                                "username": instagram_account.get("username"),
                                "name": instagram_account.get("name"),
                                "biography": instagram_account.get("biography"),
                                "website": instagram_account.get("website"),
                                "profile_picture_url": instagram_account.get("profile_picture_url"),
                                "followers_count": instagram_account.get("followers_count", 0),
                                "follows_count": instagram_account.get("follows_count", 0),
                                "media_count": instagram_account.get("media_count", 0),
                                "connected_facebook_page": {
                                    "id": page.get("id"),
                                    "name": page.get("name")
                                },
                                "page_access_token": page_token
                            }
                            
                            system_info["instagram_accounts"].append(instagram_info)
                            print(f"    ✓ Instagram: @{instagram_account.get('username')} - {instagram_account.get('followers_count', 0)} followers")
        
        return system_info
        
    except Exception as e:
        print(f"Error gathering information: {e}")
        return None

def main():
    """Main function to gather and display system user information"""
    print("=" * 60)
    print("GATHERING COMPREHENSIVE SYSTEM USER INFORMATION")
    print("=" * 60)
    
    info = get_comprehensive_system_user_info()
    
    if info:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"App: {info['app_info'].get('name')} (ID: {info['app_info'].get('id')})")
        print(f"Permissions: {len([p for p in info['permissions'] if p['status'] == 'granted'])} granted")
        print(f"Facebook Pages: {len(info['facebook_pages'])}")
        print(f"Instagram Accounts: {len(info['instagram_accounts'])}")
        
        # Save to file
        output_file = os.path.join(os.path.dirname(__file__), 'system_user_comprehensive.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Comprehensive data saved to: {output_file}")
        return info
    else:
        print("Failed to gather information")
        return None

if __name__ == '__main__':
    main()
