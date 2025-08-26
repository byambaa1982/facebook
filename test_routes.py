# Test that our changes work by importing the admin routes
try:
    from flask_app import app
    print('Flask app imported successfully')
    
    # Test the routes are properly registered
    with app.app_context():
        rules = list(app.url_map.iter_rules())
        admin_routes = [rule for rule in rules if 'admin-panel/content' in rule.rule]
        print('\nAdmin content routes found:')
        for route in admin_routes:
            print(f'  {route.rule} -> {route.endpoint} [{route.methods}]')
        
        # Test content retrieval with filename
        from routes.admin import get_unqlite_db, get_recent_contents
        db = get_unqlite_db()
        contents = get_recent_contents(db, limit=5)
        print(f'\nFound {len(contents)} contents')
        for content in contents:
            print(f'  - {content.get("title", "No title")} (filename: {content.get("filename", "None")})')
        db.close()
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
