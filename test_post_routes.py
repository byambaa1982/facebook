# Test that the post routes are working
try:
    from flask_app import app
    print('Flask app imported successfully')
    
    # Test the routes are properly registered
    with app.app_context():
        rules = list(app.url_map.iter_rules())
        post_routes = [rule for rule in rules if 'api/content' in rule.rule and 'post' in rule.rule]
        facebook_routes = [rule for rule in rules if 'facebook-apps/list' in rule.rule]
        
        print('\nPost-related routes found:')
        for route in post_routes:
            print(f'  {route.rule} -> {route.endpoint} [{route.methods}]')
            
        print('\nFacebook app routes found:')
        for route in facebook_routes:
            print(f'  {route.rule} -> {route.endpoint} [{route.methods}]')
        
        # Test that we can get Facebook apps
        from routes.post import get_facebook_apps
        apps = get_facebook_apps()
        print(f'\nFound {len(apps)} Facebook apps configured')
        for app_data in apps:
            print(f'  - {app_data.get("username", "Unknown")} (Page ID: {app_data.get("page_id", "None")})')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
